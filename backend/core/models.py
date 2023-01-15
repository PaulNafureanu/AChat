from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
class User(AbstractUser):
    email = models.EmailField(blank=True)
    pass

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='profile')
    name = models.CharField(max_length=255, blank=True)
    about = models.CharField(max_length=255, blank=True)
    friendshipRequestsSent = models.ManyToManyField('Profile', related_name='friendshipRequestsReceived')
    friends = models.ManyToManyField('Profile', related_name='+')
    restrictedProfiles = models.ManyToManyField('Profile', related_name='restrictedBy')
    activeChats = models.ManyToManyField('Chat', related_name='activeProfiles')
    archivedChats = models.ManyToManyField('Chat', related_name='archivedBy')
    # thumbnail


class Chat(models.Model):

    CHAT_TYPES = [
    (1, 'PRIVATE'),
    (2, 'GROUP'),
    # (3, 'COMMUNITY')
    ]
    name = models.CharField(max_length=255, default='Chat')
    adminProfiles = models.ManyToManyField(Profile, related_name='adminInTheChats')
    participants = models.ManyToManyField(Profile, related_name='participateInTheChats')
    chatType = models.IntegerField(choices=CHAT_TYPES)
    # thumbnail

class Message(models.Model):
    #Change m2m for messages at chat
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='messages')
    chat = models.ManyToManyField(Chat, related_name='messages')
    text = models.TextField()
    sendTime = models.DateTimeField(auto_now_add=True)
    readBy = models.ManyToManyField(Profile, related_name='messagesRead')
    readTime = models.DateTimeField(null=True, default=None)
    deliveredTo = models.ManyToManyField(Profile, related_name='messagesReceived')
    deliveredTime = models.DateTimeField(null=True, default=None)
    starredBy = models.ManyToManyField(Profile,related_name='messagesStarred')
    deleted = models.BooleanField(default=False)
