from graphene_django import DjangoObjectType, DjangoListField
import graphene
from graphene_django.filter import DjangoFilterConnectionField
from .models import Profile, Post, PostMedia, Interaction, Follow
from graphql import GraphQLError
from django.utils import timezone

from django.contrib.auth import get_user_model


User = get_user_model()




class ProfileNode(DjangoObjectType):
    mutual_followers = graphene.List(lambda: ProfileNode)
    class Meta:
        model = Profile
        fields = "__all__"
        filter_fields = {
            'first_name': ['exact', 'icontains', 'istartswith'],
            'last_name': ['exact', 'icontains', 'istartswith'],
            'user__username': ['exact', 'icontains'],
        }
        interfaces = (graphene.relay.Node,)

    def resolve_mutual_followers(self, info):
        return self.get_mutual_followers()



class PostNode(DjangoObjectType):
    media = graphene.List(lambda: PostMediaNode) # lazy reference
    engagements = graphene.List(lambda: InteractionNode)
    comments = graphene.List(lambda: PostNode)
    class Meta:
        model = Post
        fields = "__all__"
        filter_fields = {
            'content': ['exact', 'icontains', 'istartswith'],
            'author__username': ['exact', 'icontains'],
            'is_published': ['exact'],
            'created_at': ['exact', 'lt', 'gt'],
        }
        interfaces = (graphene.relay.Node,)
    
    def resolve_media(self, info):
        return self.attachments.all()
    
    def resolve_engagements(self, info):
        return self.engagements.all()
    
    def resolve_comments(self, info):
        return self.comments.all()
    

class PostMediaNode(DjangoObjectType):
    class Meta:
        model = PostMedia
        fields = "__all__"
        filter_fields = {
            'type': ['exact'],
            'post__id': ['exact'],
        }
        interfaces = (graphene.relay.Node,)




class InteractionNode(DjangoObjectType):
    class Meta:
        model = Interaction
        fields = "__all__"
        filter_fields = {
            'type': ['exact'],
            'user__username': ['exact', 'icontains'],
            'post__id': ['exact'],
            'created_at': ['exact', 'lt', 'gt'],
        }
        interfaces = (graphene.relay.Node,)

        


class FollowNode(DjangoObjectType):
    user = graphene.Field(ProfileNode)
    followed_by = graphene.Field(ProfileNode)
    class Meta:
        model = Follow 
        fields = ["id", "user", "followed_by"]
        filter_fields = {
            'user__username': ['exact', 'icontains'],
            'followed_by__username': ['exact', 'icontains']
        }
        interfaces = (
            graphene.relay.Node,
        )


    def resolve_user(self, info):
        return self.user.profile
    
    def resolve_followed_by(self, info):
        return self.followed_by.profile
    

class PostMediaInput(graphene.InputObjectType):
    media_url = graphene.String(required=True)
    type = graphene.String(required=True)
    metadata = graphene.JSONString()
    mime_type = graphene.String()


class UpdateProfile(graphene.Mutation):
    profile = graphene.Field(ProfileNode)

    class Arguments:
        first_name = graphene.String(required=False)
        last_name = graphene.String(required=False)
        profile_photo = graphene.String(required=False)
        bio = graphene.String(required=False)
        preferences = graphene.JSONString(required=False)

    def mutate(self, info, first_name=None, last_name=None, profile_photo=None, bio=None, preferences=None):
        user = info.context.user
        if user.is_anonymous or not user.is_authenticated:
            raise GraphQLError("Authentication required to update profile.")
        profile, created = Profile.objects.get_or_create(user=user) # get or create profile if not exists
        
        if first_name is not None:
            profile.first_name = first_name
        if last_name is not None:
            profile.last_name = last_name
        if profile_photo is not None:
            profile.profile_photo = profile_photo
        if bio is not None:
            profile.bio = bio
        if preferences is not None:
            profile.preferences = preferences
        
        profile.save()
        return UpdateProfile(profile=profile)

class CreatePost(graphene.Mutation):
    post = graphene.Field(PostNode)

    class Arguments:
        content = graphene.String(required=True)
        is_published = graphene.Boolean(required=False)
        parent_post_id = graphene.UUID(required=False)
        post_medias = graphene.List(PostMediaInput)

    def mutate(self, info, content, is_published=False, parent_post_id=None, post_medias=None):
        user = info.context.user
        if user.is_anonymous or not user.is_authenticated:
            raise GraphQLError("Authentication required to create a post.")
        try:
            parent_post = Post.objects.get(id=parent_post_id) if parent_post_id else None
        except Post.DoesNotExist:
            raise GraphQLError("Parent post not found.")
        post = Post.objects.create(content=content, author=user, is_published=is_published, parent_post=parent_post)

        post = Post.objects.create(
            content=content,
            author=user,
            is_published=is_published,
            created_at=timezone.now()
        )
        if post_medias:
            for media_input in post_medias:
                PostMedia.objects.create(
                    post=post,
                    media_url=media_input.get("media_url"),
                    type=media_input.get("type"),
                    metadata=media_input.get("metadata"),
                    mime_type=media_input.get("mime_type")
                )
        return CreatePost(post=post)


class UpdatePost(graphene.Mutation):
    post = graphene.Field(PostNode)

    class Arguments:
        post_id = graphene.UUID(required=True)
        content = graphene.String(required=False)
        is_published = graphene.Boolean(required=False)
    
    def mutate(self, info, post_id, content, is_published=None):
        user = info.context.user
        if user.is_anonymous or not user.is_authenticated:
            raise GraphQLError("Authentication required to update a post.")
        try:
            post = Post.objects.get(id=post_id, author=user)
        except Post.DoesNotExist:
            raise GraphQLError("Post not found or you do not have permission to edit this post.")
        
        if content:
            post.content = content
        if is_published is not None:
            post.is_published = is_published

        post.edited = True
        post.save()
        return UpdatePost(post=post)
    
class DeletePost(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        post_id = graphene.UUID(required=True)

    def mutate(self, info, post_id):
        user = info.context.user
        if user.is_anonymous or not user.is_authenticated:
            raise GraphQLError("Authentication required to delete a post.")
        try:
            post = Post.objects.get(id=post_id, author=user)
        except Post.DoesNotExist:
            raise GraphQLError("Post not found or you do not have permission to delete this post.")
        
        post.deleted = True
        post.save()
        return DeletePost(success=True)
    
class CreateInteration(graphene.Mutation):
    interaction = graphene.Field(InteractionNode)

    class Arguments:
        post_id = graphene.UUID(required=True)
        type = graphene.String(required=True)

    def mutate(self, info, post_id, type):
        user = info.context.user
        if user.is_anonymous or not user.is_authenticated:
            raise GraphQLError("Authentication required to interact with a post.")
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise GraphQLError("Post not found.")
        
        interaction = Interaction.objects.create(
            user=user,
            post=post,
            type=type
        )
        return CreateInteration(interaction=interaction)

class DeleteInteraction(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        post_id = graphene.UUID(required=True)
        type = graphene.String(required=True)
    
    def mutate(self, info, post_id, type):
        user = info.context.user
        if user.is_anonymous or not user.is_authenticated:
            raise GraphQLError("Authentication required to delete an interaction.")
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise GraphQLError("Post not found.")
        
        try:
            interaction = Interaction.objects.get(user=user, post=post, type=type)
        except Interaction.DoesNotExist:
            raise GraphQLError("Interaction not found.")
        
        interaction.delete()
        return DeleteInteraction(success=True)
    
class FollowUser(graphene.Mutation):
    success = graphene.Boolean()
    class Arguments:
        username_to_follow = graphene.String(required=True)
    
    def mutate(self, info, username_to_follow):
        user = info.context.user
        if user.is_anonymous or not user.is_authenticated:
            raise GraphQLError("Authentication required to follow a user.")
        try:
            user_to_follow = User.objects.get(username=username_to_follow)
        except User.DoesNotExist:
            raise GraphQLError("User to follow not found.")
        
        if user == user_to_follow:
            # extra check to ensure user can't follow themself, there's a database level constraint to ensure this never happens too.
            raise GraphQLError("You cannot follow yourself.")
        
        Follow.objects.get_or_create(user=user_to_follow, followed_by=user)
        return FollowUser(success=True)

class UnFollowUser(graphene.Mutation):

    success = graphene.Boolean()

    class Arguments:
        username_to_unfollow = graphene.String(required=True)
    
    def mutate(self, info, username_to_unfollow):

        user = info.context.user

        if user.is_anonymous or not user.is_authenticated:
            raise GraphQLError("Authentication required to follow a user.")
        try:
            user_to_unfollow = User.objects.get(username=username_to_unfollow)
        except User.DoesNotExist:
            raise GraphQLError("User to follow not found.")
        
        if user == user_to_unfollow:
            # extra check to ensure user can't follow themself, there's a database level constraint to ensure this never happens too.
            raise GraphQLError("You cannot unfollow yourself.")
        
        try:
            follow = Follow.objects.get(user=user_to_unfollow, followed_by=user)

        except Follow.DoesNotExist:
            raise GraphQLError("You weren't following the user")
    
        follow.delete()

        return UnFollowUser(success=True)
        



class SocialMediaMutation(graphene.ObjectType):
    update_profile = UpdateProfile.Field()
    create_post = CreatePost.Field()
    update_post = UpdatePost.Field()
    delete_post = DeletePost.Field()
    create_interaction = CreateInteration.Field()
    delete_interaction = DeleteInteraction.Field() 
    follow_user = FollowUser.Field()
    unfollow_user = UnFollowUser.Field()   


class SocialMediaQuery(graphene.ObjectType):
    profile = graphene.relay.Node.Field(ProfileNode)
    all_profiles = DjangoFilterConnectionField(ProfileNode)

    post = graphene.relay.Node.Field(PostNode)
    all_posts = DjangoFilterConnectionField(PostNode)

    post_media = graphene.relay.Node.Field(PostMediaNode)
    all_post_media = DjangoFilterConnectionField(PostMediaNode)

    interaction = graphene.relay.Node.Field(InteractionNode)
    all_interactions = DjangoFilterConnectionField(InteractionNode)

    follow = graphene.relay.Node.Field(FollowNode)
    all_follows = DjangoFilterConnectionField(FollowNode)