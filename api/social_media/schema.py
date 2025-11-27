from graphene_django import DjangoObjectType, DjangoListField
import graphene
from graphene_django.filter import DjangoFilterConnectionField
from .models import Profile, Post, PostMedia, Interaction, Follow, Bookmark
from graphql import GraphQLError
from django.utils import timezone
from graphql_jwt.decorators import login_required
from graphene.relay import Node

from django.contrib.auth import get_user_model


User = get_user_model()




class ProfileNode(DjangoObjectType):

    """GraphQL node for Profile model with mutual followers field.
    mutual_followers: List of ProfileNode representing users who mutually follow the profile owner.
    """
    mutual_followers = graphene.List(lambda: ProfileNode)
    followers = graphene.List(lambda: ProfileNode)
    following = graphene.List(lambda: ProfileNode)
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
    
    def resolve_followers(self, info):
        return self.get_followers()

    def resolve_following(self, info):
        return self.get_following()



class PostNode(DjangoObjectType):
    
    """
    GraphQL node for Post model with media, engagemenfts, and comments fields.
    media: List of PostMediaNode representing media attachments for the post.
    engagements: List of InteractionNode representing user interactions with the post.
    comments: List of PostNode representing comments on the post.
    """
    media = graphene.List(lambda: PostMediaNode) # lazy reference
    engagements = graphene.List(lambda: InteractionNode)
    comments = graphene.List(lambda: PostNode)
    likes = graphene.Int()
    class Meta:
        model = Post
        fields = "__all__"
        filter_fields = {
            'content': ['exact', 'icontains', 'istartswith'],
            'author__username': ['exact', 'icontains'],
            'is_published': ['exact'],
            'created_at': ['exact', 'lt', 'gt'],
            'deleted': ['exact'],
        }
        interfaces = (graphene.relay.Node,)
    
    def resolve_media(self, info):
        return self.attachments.all()
    
    def resolve_engagements(self, info):
        return self.engagements.all()
    
    def resolve_comments(self, info):
        return self.comments.all()
    
    def resolve_likes(self, info):
        return self.likes()

class PostMediaNode(DjangoObjectType):

    """
    GraphQL node for PostMedia model.
    media_url: URL of the media attachment.
    type: Type of media (PHOTO, VIDEO, GIF).
    metadata: Additional metadata for the media attachment.
    mime_type: MIME type of the media attachment.  

    """
    class Meta:
        model = PostMedia
        fields = "__all__"
        filter_fields = {
            'type': ['exact'],
            'post__id': ['exact'],
        }
        interfaces = (graphene.relay.Node,)




class InteractionNode(DjangoObjectType):

    """
    GraphQL node for Interaction model.
    type: Type of interaction (LIKE, SHARE, COMMENT).
    user: ProfileNode representing the user who made the interaction.
    post: PostNode representing the post that was interacted with.
    """
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
    """
    GraphQL node for Follow model.
    user: ProfileNode representing the user being followed.
    followed_by: ProfileNode representing the user who is following.
    """

    user = graphene.Field(ProfileNode)
    followed_by = graphene.Field(ProfileNode)
    class Meta:
        model = Follow 
        fields = ["id", "user", "followed_by"]
        filter_fields = {
            'user__username': ['iexact', 'icontains'],
            'followed_by__username': ['exact', 'icontains']
        }
        interfaces = (
            graphene.relay.Node,
        )


    def resolve_user(self, info):
        return self.user.profile
    
    def resolve_followed_by(self, info):
        return self.followed_by.profile
    

class BookmarkNode(DjangoObjectType):
    class Meta:
        model = Bookmark 
        fields = "__all__"
        filter_fields = {
            "user__username": ['iexact', 'icontains'],
            "post__id": ['exact']
        }
        interfaces = (
            graphene.relay.Node
        )


class PostMediaInput(graphene.InputObjectType):
    """
    PostMediaInput: Input type for creating PostMedia attachments.
    media_url: URL of the media attachment.
    type: Type of media (PHOTO, VIDEO, GIF).
    metadata: Additional metadata for the media attachment.
    mime_type: MIME type of the media attachment.

    """
    media_url = graphene.String(required=True)
    type = graphene.String(required=True)
    metadata = graphene.JSONString()
    mime_type = graphene.String()


class UpdateProfile(graphene.Mutation):

    """
    Mutation to update user profile information.
    first_name: Updated first name of the user.
    last_name: Updated last name of the user.
    profile_photo: Updated profile photo URL.
    bio: Updated biography of the user.
    preferences: Updated user preferences in JSON format.

    """
    profile = graphene.Field(ProfileNode)

    class Arguments:
        first_name = graphene.String(required=False)
        last_name = graphene.String(required=False)
        profile_photo = graphene.String(required=False)
        bio = graphene.String(required=False)
        preferences = graphene.JSONString(required=False)

    @login_required
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

    """
    GraphQL mutation to create a new post.
    content: Content of the post.
    is_published: Boolean indicating if the post is published.
    parent_post_id: ID of the parent post if it's a comment.
    post_medias: List of PostMediaInput for media attachments.
    
    """
    post = graphene.Field(PostNode)

    class Arguments:
        content = graphene.String(required=True)
        is_published = graphene.Boolean(required=False)
        parent_post_id = graphene.ID(required=False)
        post_medias = graphene.List(PostMediaInput)

    @login_required
    def mutate(self, info, content, is_published=False, parent_post_id=None, post_medias=None):
        user = info.context.user
        if parent_post_id:
            _, parent_post_id = Node.from_global_id(parent_post_id)
        if user.is_anonymous or not user.is_authenticated:
            raise GraphQLError("Authentication required to create a post.")
        try:
            parent_post = Post.objects.get(id=parent_post_id) if parent_post_id else None
        except Post.DoesNotExist:
            raise GraphQLError("Parent post not found.")
        post = Post.objects.create(content=content, author=user, is_published=is_published, parent_post=parent_post)
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

    """
    
    Mutation to update an existing post.
    post_id: ID of the post to be updated.
    content: Updated content of the post.
    is_published: Updated published status of the post.
    """
    post = graphene.Field(PostNode)

    class Arguments:
        post_id = graphene.ID(required=True)
        content = graphene.String(required=False)
        is_published = graphene.Boolean(required=False)

    @login_required 
    def mutate(self, info, post_id, content, is_published=None):
        _, post_id = Node.from_global_id(post_id) # decode the global ID to get the actual post ID (node, modeluuid)
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
    """
    GraphQL mutation to soft delete a post.
    post_id: ID of the post to be deleted.
    object is not permanently removed but marked as deleted.
    after 30 days, a Celery task will permanently delete it.
    """
    success = graphene.Boolean()

    class Arguments:
        post_id = graphene.ID(required=True)

    @login_required
    def mutate(self, info, post_id):
        user = info.context.user
        if user.is_anonymous or not user.is_authenticated:
            raise GraphQLError("Authentication required to delete a post.")

        _, post_id = Node.from_global_id(post_id) # decode the global ID to get the actual post ID (node, modeluuid)
        try:
            post = Post.objects.get(id=post_id, author=user)
        except Post.DoesNotExist:
            raise GraphQLError("Post not found or you do not have permission to delete this post.")
        
        post.deleted = True
        post.save()
        return DeletePost(success=True)
    
class CreateInteration(graphene.Mutation):
    """
    GraphQL mutation to create an interaction on a post.
    post_id: ID of the post to interact with.
    type: Type of interaction (LIKE, SHARE, COMMENT).

    """
    interaction = graphene.Field(InteractionNode)

    class Arguments:
        post_id = graphene.ID(required=True)
        type = graphene.String(required=True)

    @login_required
    def mutate(self, info, post_id, type):
        user = info.context.user
        if user.is_anonymous or not user.is_authenticated:
            raise GraphQLError("Authentication required to interact with a post.")
        _, post_id = Node.from_global_id(post_id) 
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
    """
    GraphQL mutation to delete an interaction on a post.
    post_id: ID of the post associated with the interaction.
    type: Type of interaction to be deleted (LIKE, SHARE, COMMENT).

    Deleting interaction here is only applicable to the following scenarios:
    - A user wants to unlike a post they previously liked.
    - A user wants delete a comment they previously made on a post.
        -> Deleting a comment will involve deleting the post itself then deleting the interaction associated to the post under the interaction type comment

    """
    success = graphene.Boolean()

    class Arguments:
        post_id = graphene.ID(required=True)
        type = graphene.String(required=True)
    

    @login_required
    def mutate(self, info, post_id, type):
        user = info.context.user
        if user.is_anonymous or not user.is_authenticated:
            raise GraphQLError("Authentication required to delete an interaction.")
        
        _, post_id = Node.from_global_id(post_id)
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

    """
    GraphQL mutation to follow a user.
    username_to_follow: Username of the user to follow.

    The user cannot follow themself.

    """
    success = graphene.Boolean()
    class Arguments:
        username_to_follow = graphene.String(required=True)
    

    @login_required
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

    """
    GraphQL mutation to unfollow a user.
    username_to_unfollow: Username of the user to unfollow.
    The user cannot unfollow themself.
    """
    success = graphene.Boolean()

    class Arguments:
        username_to_unfollow = graphene.String(required=True)
    

    @login_required
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
    
class AddPostToBookmark(graphene.Mutation):

    bookmark = graphene.Field(BookmarkNode)
    success = graphene.Boolean()

    class Arguments:
        post_id = graphene.ID(required=True)

    @login_required
    def mutate(self, info, post_id):
        user = info.context.user

        if user.is_anonymous or not user.is_authenticated:
            raise GraphQLError("Authentication required to bookmark a post.")
        
        _, post_id = Node.from_global_id(post_id)
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise GraphQLError("Post not found.")
        
        bookmark, created = Bookmark.objects.get_or_create(user=user, post=post)
        if not created:
            raise GraphQLError("Post already bookmarked.")
        
        return AddPostToBookmark(bookmark=bookmark, success=True)
    

class RemovePostFromBookmark(graphene.Mutation):

    success = graphene.Boolean()

    class Arguments:
        post_id = graphene.ID(required=True)


    @login_required
    def mutate(self, info, post_id):
        user = info.context.user

        if user.is_anonymous or not user.is_authenticated:
            raise GraphQLError("Authentication required to remove bookmark.")
        
        _, post_id = Node.from_global_id(post_id)
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise GraphQLError("Post not found.")
        
        try:
            bookmark = Bookmark.objects.get(user=user, post=post)
        except Bookmark.DoesNotExist:
            raise GraphQLError("Bookmark not found.")
        
        bookmark.delete()
        return RemovePostFromBookmark(success=True)
        



class SocialMediaMutation(graphene.ObjectType):
    update_profile = UpdateProfile.Field()
    create_post = CreatePost.Field()
    update_post = UpdatePost.Field()
    delete_post = DeletePost.Field()
    create_interaction = CreateInteration.Field()
    delete_interaction = DeleteInteraction.Field() 
    follow_user = FollowUser.Field()
    unfollow_user = UnFollowUser.Field() 
    add_post_to_bookmark = AddPostToBookmark.Field()
    remove_post_from_bookmark = RemovePostFromBookmark.Field()  


class SocialMediaQuery(graphene.ObjectType):
    profile = graphene.relay.Node.Field(ProfileNode)
    all_profiles = DjangoFilterConnectionField(ProfileNode)

    post = graphene.relay.Node.Field(PostNode)
    all_posts = DjangoFilterConnectionField(PostNode)
    all_posts_including_comments = DjangoFilterConnectionField(PostNode) # Returns all posts including post returned as comments... for filtering and paginating
    all_deleted_posts = DjangoFilterConnectionField(PostNode) 

    post_media = graphene.relay.Node.Field(PostMediaNode)
    all_post_media = DjangoFilterConnectionField(PostMediaNode)

    interaction = graphene.relay.Node.Field(InteractionNode)
    all_interactions = DjangoFilterConnectionField(InteractionNode)

    follow = graphene.relay.Node.Field(FollowNode)
    all_follows = DjangoFilterConnectionField(FollowNode)

    bookmark = graphene.relay.Node.Field(BookmarkNode)
    all_bookmarks = DjangoFilterConnectionField(BookmarkNode)


    @login_required
    def resolve_profile(self, info, id):
        return ProfileNode.get_node(info, id)

    @login_required
    def resolve_all_profiles(self, info, **kwargs):
        return Profile.objects.all()
    
    @login_required
    def resolve_all_posts(self, info, **kwargs):
        return Post.objects.filter(deleted=False, parent_post=None)
    

    @login_required
    def resolve_all_posts_including_comments(self, info, **kwargs):
        return Post.objects.filter(deleted=False)
    

    @login_required
    def resolve_all_deleted_posts(self, info, **kwargs):
        return Post.objects.filter(deleted=True)

    @login_required
    def resolve_post(self, info, id):
        return PostNode.get_node(inf, id)

    @login_required
    def resolve_all_interactions(self, info, **kwargs):
        return Interaction.objects.select_related("post", "user").all()
    
    @login_required
    def resolve_interaction(self, info, id):
        return InteractionNode.get_node(info, id)


    @login_required
    def resolve_all_follows(self, info, **kwargs):
        return Follow.objects.select_related("user__profile", "followed_by__profile").all()
    
    @login_required
    def resolve_follow(self, info, id):
        return FollowNode.get_node(info, id)
    
    @login_required
    def resolve_all_post_media(self, info, **kwargs):
        return PostMedia.objects.select_related("post").all()
    
    @login_required
    def resolve_post_media(self, info, **kwargs):
        return PostMediaNode.get_node(info, id)
    
    @login_required
    def resolve_bookmark(self, info, **kwargs):
        user = info.context.user

        bookmark =  BookmarkNode.get_node(info, id)
        if user != bookmark.user:
            raise GraphQLError("You don't have permission to view this bookmark")
        return bookmark
    

    @login_required
    def resolve_all_bookmarks(self, info, **kwargs):
        user = info.context.user
        return Bookmark.objects.select_related("user", "post").filter(user=user) # bookmarks are private
    

