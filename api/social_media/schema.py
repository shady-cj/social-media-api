from graphene_django import DjangoObjectType, DjangoListField
import graphene
from graphene_django.filter import DjangoFilterConnectionField
from .models import Profile, Post, PostMedia, Interaction, Follow
import re
from graphql import GraphQLError
from django.utils import timezone
# from .filters import CustomerFilter, ProductFilter, OrderFilter




class ProfileNode(DjangoObjectType):
    mutual_followers = DjangoListField(lambda: ProfileNode)
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
    media = DjangoListField(lambda: PostMediaNode) # lazy reference
    engagements = DjangoListField(lambda: InteractionNode)
    comments = DjangoListField(lambda: PostNode)
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
        interfaces = [
            graphene.relay.Node
        ]


    def resolve_user(self, info):
        return self.user.profile
    
    def resolve_followed_by(self, info):
        return self.followed_by.profile
    


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