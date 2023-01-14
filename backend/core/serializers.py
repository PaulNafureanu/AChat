from django.core.exceptions import PermissionDenied
from rest_framework import serializers
from .models import *

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["userId", "name", "about"] #add thumbnail
    
    userId = serializers.IntegerField(required = True, source="user.id")

    def create(self, validated_data):
        user = User.objects.get(pk = validated_data["user"]["id"])
        if(Profile.objects.filter(pk = user).exists()):
            raise Exception({'userId':'Already an entry profile with this user id.'})
        del validated_data["user"]
        profile = Profile(**validated_data)
        profile.user = user
        if(not validated_data.get('name')):
            profile.name = user.username
        if(not validated_data.get('about')):
            profile.about = "Hi! Here should be something about me."
        #set the thumbnail as well
        profile.save()
        return profile
    
class MyProfileSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source='user.id', read_only = True)
    # #add thumbnail
    friendshipRequestsSent = serializers.PrimaryKeyRelatedField(many = True, read_only = True)
    friendshipRequestsReceived = serializers.PrimaryKeyRelatedField(many = True, read_only = True)
    friends = serializers.PrimaryKeyRelatedField(many = True, read_only = True)
    restrictedProfiles = serializers.PrimaryKeyRelatedField(many = True, read_only = True)
    activeChats = serializers.PrimaryKeyRelatedField(many = True, read_only = True)
    archivedChats = serializers.PrimaryKeyRelatedField(many = True, read_only = True)

    class Meta:
        model = Profile
        fields = ['userId', 'name', 'about', 'friendshipRequestsSent', 'friendshipRequestsReceived', 'friends', 'restrictedProfiles', 'activeChats', 'archivedChats']


