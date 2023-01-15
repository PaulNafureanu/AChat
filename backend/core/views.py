from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from .models import *
from .serializers import *

# Create your views here.

@api_view(['POST', 'GET'])
def profiles(request:Request):
    try:
        if(request.method == 'POST'):
            serializer = ProfileSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        elif(request.method == 'GET'):
            page = request.query_params.get('page')
            search = request.query_params.get('search')

            if not page: page = 1
            else: page = int(page)
            if not search: search = ''

            queryset = Profile.objects.select_related("user").filter(user__username__icontains = search)

            if(request.user.is_authenticated):
                user = get_object_or_404(User, pk = request.user.id)
                profile = get_object_or_404(Profile, pk = user)
                queryset = queryset.exclude(restrictedProfiles__pk = profile)

            queryset = queryset[(page - 1)*50:page*50]

            serializer = ProfileSerializer(queryset, many = True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as error:
        return Response(error.args, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
def specificProfiles(request:Request, userId:int):
    try:
        if(request.user.is_authenticated):
            authenticatedUserId = request.user.id
            if(request.method == 'GET'):
                # Get a specific profile
                user = get_object_or_404(User, pk = authenticatedUserId)
                targetUser = get_object_or_404(User, pk = userId)
                targetProfile = get_object_or_404(Profile, pk = targetUser)
                if(targetProfile.restrictedProfiles.filter(pk = user).exists()):
                    raise Exception({'detail': 'The target profile restricted access for your profile.'})
                serializer = MyProfileSerializer(targetProfile) if(userId == request.user.id) else ProfileSerializer(targetProfile)
                return Response(serializer.data, status=status.HTTP_200_OK)
            
            if(authenticatedUserId != userId): raise PermissionDenied({'user':'User is not authenticated properly.'})
            
            if(request.method == 'PATCH'):
                # Update the authenticated profile
                user = get_object_or_404(User, pk = authenticatedUserId)
                profile = get_object_or_404(Profile, pk = user)
                serializer = MyProfileSerializer(profile, data = request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data, status = status.HTTP_200_OK)
            
            elif(request.method == 'DELETE'):
                # Delete the authenticated profile
                user = get_object_or_404(User, pk = authenticatedUserId)
                profile = get_object_or_404(Profile, pk = user)
                profile.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            
        else: raise PermissionDenied({'detail': 'User not authenticated.'})
    except PermissionDenied as error:
        return Response(error.args, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as error:
        return Response(error.args, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def friendshipRequests(request:Request, userId:int):
    try:
        if(request.user.is_authenticated and request.user.id == userId):
            if(request.method == 'GET'):
                page = request.query_params.get('page')
                search = request.query_params.get('search')
                listType = request.query_params.get('list')

                if not page: page = 1
                else: page = int(page)
                if not search: search = ''
                if not listType: raise KeyError({'detail':'"List" query parameter is required in the URL. Set it to either "sent" or "received".' })
            
                user = get_object_or_404(User, pk = userId)
                profile = get_object_or_404(Profile, pk = user)
                
                if(listType == 'sent'):
                    queryset =  profile.friendshipRequestsSent
                elif(listType == 'received'):
                    queryset = profile.friendshipRequestsReceived
                else: raise KeyError({'detail':'"List" query parameter should be set to either "sent" or "received".' })

                serializer = ProfileSerializer(queryset, many = True)
                return Response(serializer.data, status = status.HTTP_200_OK)

        else: raise PermissionDenied({'detail':'User not authenticated.'})
    except PermissionDenied as error:
        return Response(error.args, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as error:
        return Response(error.args, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST', 'DELETE'])
def specificFriendshipRequests(request:Request, userId: int, targetUserId:int):
    try:
        if(request.user.is_authenticated and request.user.id == userId):
            
            if(targetUserId == userId): raise Exception({'detail': 'You can not send / accept / undo or not accept a friendship request to and from yourself.'})

            listType = request.query_params.get('list')
            if (not listType == 'sent') and (not listType == 'received'): raise KeyError({'detail':'"List" query parameter is required in the URL. Set it to either "sent" or "received".' })
            
            user = get_object_or_404(User, pk = userId)
            profile = get_object_or_404(Profile, pk = user)

            targetUser = get_object_or_404(User, pk = targetUserId)
            targetProfile = get_object_or_404(Profile, pk = targetUser)

            if(request.method == 'POST'):
                if(listType == 'sent'):
                    # Send a friendship request from profile to target profile
                    if(profile.friends.filter(pk = targetUser).exists()):
                        raise Exception({'detail':'You can not send a friendship request to a friend.'})
                    if(targetProfile.restrictedProfiles.filter(pk = profile).exists()):
                        raise Exception({'detail': 'The target profile restricted access for your profile.'})
                    profile.friendshipRequestsSent.add(targetProfile)
                    targetProfile.friendshipRequestsReceived.add(profile)
                    profile.save()
                    targetProfile.save()
                    serializer = MyProfileSerializer(profile)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                elif(listType == 'received'):
                    # Accept a friendship request from target profile
                    profile.friends.add(targetProfile)
                    targetProfile.friends.add(profile)
                    profile.friendshipRequestsReceived.remove(targetProfile)
                    targetProfile.friendshipRequestsSent.remove(profile)
                    profile.save()
                    targetProfile.save()
                    serializer = MyProfileSerializer(profile)
                    return Response(serializer.data, status=status.HTTP_200_OK)
            elif(request.method == 'DELETE'):
                if(listType == 'sent'):
                    # Undo a friendship request sent from profile to target profile
                    profile.friendshipRequestsSent.remove(targetProfile)
                    targetProfile.friendshipRequestsReceived.remove(profile)
                    profile.save()
                    targetProfile.save()
                    serializer = MyProfileSerializer(profile)
                    return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
                elif(listType == 'received'):
                    # Not accept a friendship request from target profile
                    profile.friendshipRequestsReceived.remove(targetProfile)
                    targetProfile.friendshipRequestsSent.remove(profile)
                    profile.save()
                    targetProfile.save()
                    serializer = MyProfileSerializer(profile)
                    return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
        else: raise PermissionDenied({'detail':'User not authenticated.'})
    except PermissionDenied as error:
        return Response(error.args, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as error:
        return Response(error.args, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def friends(request:Request, userId:int):
    try:
        if(request.user.is_authenticated and request.user.id == userId):

            page = request.query_params.get('page')
            search = request.query_params.get('search')

            if(not page): page = 1
            else: page = int(page)
            if(not search): search = ""

            if(request.method == 'GET'):
                user = get_object_or_404(User, pk = userId)
                profile = get_object_or_404(Profile, pk = user)
                queryset = profile.friends.select_related('user').filter(user__username__icontains = search)[(page-1)*50:page*50]
                serializer = ProfileSerializer(queryset, many = True)
                return Response(serializer.data, status=status.HTTP_200_OK)

        else: raise PermissionDenied({'detail':'User not authenticated.'})
    except PermissionDenied as error:
        return Response(error.args, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as error:
        return Response(error.args, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['DELETE'])
def specificFriends(request:Request, userId:int, targetUserId: int):
    try:
        if(request.user.is_authenticated and request.user.id == userId):
            if(request.method == 'DELETE'):
                user = get_object_or_404(User, pk = userId)
                profile = get_object_or_404(Profile, pk = user)
                targetUser = get_object_or_404(User, pk = targetUserId)
                targetProfile = get_object_or_404(Profile, pk = targetUser)
                profile.friends.remove(targetProfile)
                targetProfile.friends.remove(profile)
                profile.save()
                targetProfile.save()
                serializer = MyProfileSerializer(profile)
                return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
        else: raise PermissionDenied({'detail': 'User not authenticated'})
    except PermissionDenied as error:
        return Response(error.args, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as error:
        return Response(error.args, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def restrictedProfiles(request:Request, userId:int):
    try:
        if(request.user.is_authenticated and request.user.id == userId):
            page = request.query_params.get('page')
            search = request.query_params.get('search')

            if not page: page = 1
            else: page = int(page)
            if not search: search = ''

            if(request.method == 'GET'):
                user = get_object_or_404(User, pk = userId)
                profile = get_object_or_404(Profile, pk = user)

                queryset = profile.restrictedProfiles.select_related('user').filter(user__username__icontains = search)[(page - 1)*50:page*50]
                serializer = ProfileSerializer(queryset, many = True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            
        else: raise PermissionDenied({'detail':'User not authenticated.'})
    except PermissionDenied as error:
        return Response(error.args, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as error:
        return Response(error.args, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST','DELETE'])
def specificRestrictedProfiles(request:Request, userId:int, targetUserId:int):
    try:
        if(request.user.is_authenticated and request.user.id == userId):
            if(targetUserId == userId): raise Exception({'detail':'You can not restrict / unrestrict your own profile.'})

            user = get_object_or_404(User, pk = userId)
            profile = get_object_or_404(Profile, pk = user)
            targetUser = get_object_or_404(User, pk = targetUserId)
            targetProfile = get_object_or_404(Profile, pk = targetUser)

            if(request.method == 'POST'):
                # Restrict a target profile
                profile.restrictedProfiles.add(targetProfile)
                profile.friends.remove(targetProfile)
                targetProfile.friends.remove(profile)
                profile.save()
                targetProfile.save()
                serializer = MyProfileSerializer(profile)
                return Response(serializer.data, status=status.HTTP_200_OK)
            
            elif(request.method == 'DELETE'):
                # Unrestrict (remove restriction) a target profile
                profile.restrictedProfiles.remove(targetProfile)
                profile.save()
                serializer = MyProfileSerializer(profile)
                return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
            
        else: raise PermissionDenied({'detail':'User not authenticated.'})
    except PermissionDenied as error:
        return Response(error.args, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as error:
        return Response(error.args, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST', 'GET', 'PUT', 'PATCH'])
def chats(request:Request):
    try:
        if(request.user.is_authenticated):
            authenticatedUserId = request.user.id
            user = get_object_or_404(User, pk = authenticatedUserId)
            profile = get_object_or_404(Profile, pk = user)

            page = request.query_params.get('page')
            search = request.query_params.get('search')
            listType = request.query_params.get('list')

            if(not page): page = 1
            else: page = int(page)
            if(not search): search = ""
            if((not listType == 'active') and (not listType == 'archived')): raise Exception({'detail':'"List" is required as a query string parameter in the URL. Set it to either "active" or "archived".'})

            if(request.method == 'POST'):
                # Create a chat
                serializer = ChatSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                profile.activeChats.add(serializer.instance)
                serializer.instance.adminProfiles.add(profile)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            elif(request.method == 'GET'):
                # Get the list of active / archived chats
                if(listType == 'active'):
                    queryset = profile.activeChats.filter(name__icontains = search)[(page - 1)*50:page*50]
                elif(listType == 'archived'):
                    queryset = profile.archivedChats.filter(name__icontains = search)[(page - 1)*50:page*50]
                serializer = ChatSerializer(queryset, many = True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            
            elif(request.method == 'PUT'):
                # Put has the role of activating / archiving chats
                chatIdList = request.data.get('chatIdList')
                if(not chatIdList): raise ValueError('The "chatIdList" is required and should not be empty.')

                if(listType == 'active'):
                    queryset = profile.activeChats.filter(pk__in = chatIdList)
                    for chat in queryset.iterator():
                        profile.archivedChats.add(chat)
                        profile.activeChats.remove(chat)
                    serializer = MyProfileSerializer(profile)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                elif(listType == 'archived'):
                    queryset = profile.archivedChats.filter(pk__in = chatIdList)
                    for chat in queryset.iterator():
                        profile.activeChats.add(chat)
                        profile.archivedChats.remove(chat)
                    serializer = MyProfileSerializer(profile)
                    return Response(serializer.data, status=status.HTTP_200_OK)
            
            elif(request.method == 'PATCH'):
                # Patch has the role of delete because there is not a body in HTTP Delete to send an array with ids for deletion of multiple items/entries
                chatIdList = request.data.get('chatIdList')
                if(not chatIdList): raise ValueError('The "chatIdList" is required and should not be empty.')

                if(listType == 'active'):
                    queryset = profile.activeChats.filter(pk__in = chatIdList)
                    for chat in queryset.iterator():
                        chat.adminProfiles.remove(profile)
                        chat.participants.remove(profile)
                        profile.activeChats.remove(chat)

                        thereAreNoAdmins = chat.adminProfiles.count() == 0
                        thereAreNoParticipants = chat.participants.count() == 0

                        if(thereAreNoAdmins and thereAreNoParticipants):
                            chat.delete()
                        elif(thereAreNoAdmins):
                            profile = chat.participants.all()[0]
                            chat.adminProfiles.add(profile)
                            chat.participants.remove(profile)

                    serializer = MyProfileSerializer(profile)
                    return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
                elif(listType == 'archived'):
                    queryset = profile.archivedChats.filter(pk__in = chatIdList)
                    for chat in queryset.iterator():
                        chat.adminProfiles.remove(profile)
                        chat.participants.remove(profile)
                        profile.archivedChats.remove(chat)

                        thereAreNoAdmins = chat.adminProfiles.count() == 0
                        thereAreNoParticipants = chat.participants.count() == 0

                        if(thereAreNoAdmins and thereAreNoParticipants):
                            chat.delete()
                        elif(thereAreNoAdmins):
                            profile = chat.participants.all()[0]
                            chat.adminProfiles.add(profile)
                            chat.participants.remove(profile)
                        
                    serializer = MyProfileSerializer(profile)
                    return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
                


            return Response('ok')
        else: raise PermissionDenied({'detail':'User not authenticated.'})
    except PermissionDenied as error:
        return Response(error.args, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as error:
        return Response(error.args, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST', 'GET', 'PUT', 'PATCH'])
def specificChats(request:Request, chatId:int):
    try:
        if(request.user.is_authenticated):
            page = request.query_params.get('page')
            search = request.query_params.get('search')
            listType = request.query_params.get('list')

            if(not page): page = 1
            else: page = int(page)
            if(not search): search = ""
            if((not listType == 'admin') and (not listType == 'participant')): raise ValueError('"List" is required as a query string parameter. Set it to "admin" or "participant".')

            
            authenticatedUserId = request.user.id
            profile = get_object_or_404(Profile, pk = authenticatedUserId)
            chat = get_object_or_404(Chat, pk = chatId)
            hasProfileParticipantPermission = chat.participants.filter(pk = profile).exists()
            hasProfileAdminPermission = chat.adminProfiles.filter(pk = profile).exists()

            if(request.method == 'GET'):
                # Get admins/participants
                if(not hasProfileParticipantPermission and not hasProfileAdminPermission):
                    raise PermissionDenied('The user is not a participant.')
                if(listType == 'admin'):
                    queryset = chat.adminProfiles.filter(user__username__icontains = search)[(page - 1)*50: page*50]
                elif(listType == 'participant'):
                    queryset = chat.participants.filter(user__username__icontains = search)[(page - 1)*50: page*50]
                serializer = ProfileSerializer(queryset, many = True)
                return Response(serializer.data, status = status.HTTP_200_OK)
                
            userIdList = request.data.get('userIdList')
            if(not userIdList): raise ValueError('The "userIdList" is required and should not be empty.')
            isProfileActingOnlyOnItself = userIdList[0] == authenticatedUserId and len(userIdList) == 1

            if(request.method == 'POST'):
                # Add a new admin/participant
                if(not hasProfileAdminPermission):
                    raise PermissionDenied('The user is not an admin for modifying chat participants.')
                
                queryset = Profile.objects.filter(pk__in = userIdList)
                if(listType == 'admin'):
                    for profile in queryset.iterator():
                        chat.adminProfiles.add(profile)
                        chat.participants.remove(profile)
                        profile.activeChats.add(chat)
                        profile.archivedChats.remove(chat)
                if(listType == 'participant'):
                    for profile in queryset.iterator():
                        chat.participants.add(profile)
                        chat.adminProfiles.remove(profile)
                        profile.activeChats.add(chat)
                        profile.archivedChats.remove(chat)
                return Response(status=status.HTTP_200_OK)
            
            elif(request.method == 'PUT'):
                # Change status and permissions of a chat admin/participant
                if(not hasProfileAdminPermission):
                    raise PermissionDenied('The user is not an admin for modifying chat participants.')
                
                if(listType == 'admin'):
                    queryset = chat.adminProfiles.filter(pk__in = userIdList)
                    for profile in queryset.iterator():
                        chat.participants.add(profile)
                        chat.adminProfiles.remove(profile)
                elif(listType == 'participant'):
                    queryset = chat.participants.filter(pk__in = userIdList)
                    for profile in queryset.iterator():
                        chat.adminProfiles.add(profile)
                        chat.participants.remove(profile)
                return Response(status=status.HTTP_200_OK)
                    

            elif(request.method == 'PATCH'):
                # Patch has the role of delete because there is not a body in HTTP Delete to send an array with ids for deletion/removing of multiple items/entries
                if((not hasProfileAdminPermission) and (not isProfileActingOnlyOnItself)):
                    raise PermissionDenied('The user is not an admin for modifying chat participants.')
                
                if(listType == 'admin'):
                    queryset = chat.adminProfiles.filter(pk__in = userIdList)
                if(listType == 'participant'):
                    queryset = chat.participants.filter(pk__in = userIdList)

                for profile in queryset.iterator():
                    chat.adminProfiles.remove(profile)
                    chat.participants.remove(profile)

                if(authenticatedUserId in userIdList):
                    profile.activeChats.remove(chat)
                    profile.archivedChats.remove(chat)

                thereAreNoAdmins = chat.adminProfiles.count() == 0
                thereAreNoParticipants = chat.participants.count() == 0
            
                if(thereAreNoAdmins and thereAreNoParticipants):
                    chat.delete()
                elif(thereAreNoAdmins):
                    profile = chat.participants.all()[0]
                    chat.adminProfiles.add(profile)
                    chat.participants.remove(profile)

                return Response(status=status.HTTP_204_NO_CONTENT)

        else: raise PermissionDenied({'detail':'User not authenticated.'})
    except PermissionDenied as error:
        return Response(error.args, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as error:
        return Response(error.args, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST', 'GET', 'PUT', 'PATCH'])
def messages(request:Request, chatId:int):
    try:
        if(request.user.is_authenticated):
            authenticatedUserId = request.user.id
            user = get_object_or_404(User, pk = authenticatedUserId)
            profile = get_object_or_404(Profile, pk = user)
            chat = get_object_or_404(Chat, pk = chatId)
            hasProfileParticipantPermission = chat.participants.filter(pk = profile).exists()
            hasProfileAdminPermission = chat.adminProfiles.filter(pk = profile).exists()
            if(not hasProfileAdminPermission and not hasProfileParticipantPermission):
                raise PermissionDenied({'detail':'User is not a participant.'})

            if(request.method == 'POST'):
                request.data["profile"] = profile
                serializer = MessageSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            elif(request.method == 'GET'):
                return Response('ok')


        else: raise PermissionDenied({'detail':'User not authenticated.'})
    except PermissionDenied as error:
        return Response(error.args, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as error:
        return Response(error.args, status=status.HTTP_400_BAD_REQUEST)