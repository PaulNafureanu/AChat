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

            queryset = Profile.objects.select_related("user").filter(user__username__icontains = search)[(page - 1)*50:page*50]
            serializer = ProfileSerializer(queryset, many = True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as error:
        return Response(error.args, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
def specificProfiles(request:Request, userId:int):
    try:
        if(request.user.is_authenticated):
            if(request.method == 'GET'):
                user = get_object_or_404(User, pk = userId)
                profile = get_object_or_404(Profile, pk = user)
                serializer = MyProfileSerializer(profile) if(userId == request.user.id) else ProfileSerializer(profile)
                return Response(serializer.data, status=status.HTTP_200_OK)
            
            authenticatedUserId = request.user.id
            if(authenticatedUserId != userId): raise PermissionDenied({'user':'User is not authenticated properly.'})
            
            if(request.method == 'PATCH'):
                user = get_object_or_404(User, pk = authenticatedUserId)
                profile = get_object_or_404(Profile, pk = user)
                serializer = MyProfileSerializer(profile, data = request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data, status = status.HTTP_200_OK)
            
            elif(request.method == 'DELETE'):
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
            
            listType = request.query_params.get('list')
            if (not listType == 'sent') and (not listType == 'received'): raise KeyError({'detail':'"List" query parameter is required in the URL. Set it to either "sent" or "received".' })
            
            user = get_object_or_404(User, pk = userId)
            profile = get_object_or_404(Profile, pk = user)

            targetUser = get_object_or_404(User, pk = targetUserId)
            targetProfile = get_object_or_404(Profile, pk = targetUser)

            if(request.method == 'POST'):
                if(listType == 'sent'):
                    profile.friendshipRequestsSent.add(targetProfile)
                    targetProfile.friendshipRequestsReceived.add(profile)
                    profile.save()
                    targetProfile.save()
                    serializer = MyProfileSerializer(profile)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                elif(listType == 'received'):
                    profile.friends.add(targetProfile)
                    profile.friendshipRequestsReceived.remove(targetProfile)
                    targetProfile.friendshipRequestsSent.remove(profile)
                    profile.save()
                    targetProfile.save()
                    serializer = MyProfileSerializer(profile)
                    return Response(serializer.data, status=status.HTTP_200_OK)
            elif(request.method == 'DELETE'):
                if(listType == 'sent'):
                    profile.friendshipRequestsSent.remove(targetProfile)
                    targetProfile.friendshipRequestsReceived.remove(profile)
                    profile.save()
                    targetProfile.save()
                    serializer = MyProfileSerializer(profile)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                elif(listType == 'received'):
                    profile.friendshipRequestsReceived.remove(targetProfile)
                    targetProfile.friendshipRequestsSent.remove(profile)
                    profile.save()
                    targetProfile.save()
                    serializer = MyProfileSerializer(profile)
                    return Response(serializer.data, status=status.HTTP_200_OK)
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
                profile.save()
                serializer = MyProfileSerializer(profile)
                return Response(serializer.data, status=status.HTTP_200_OK)
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
            user = get_object_or_404(User, pk = userId)
            profile = get_object_or_404(Profile, pk = user)
            targetUser = get_object_or_404(User, pk = targetUserId)
            targetProfile = get_object_or_404(Profile, pk = targetUser)

            if(request.method == 'POST'):
                profile.restrictedProfiles.add(targetProfile)
                targetProfile.friends.remove(profile)
                profile.save()
                targetProfile.save()
                serializer = MyProfileSerializer(profile)
                return Response(serializer.data, status=status.HTTP_200_OK)
            elif(request.method == 'DELETE'):
                profile.restrictedProfiles.remove(targetProfile)
                profile.save()
                serializer = MyProfileSerializer(profile)
                return Response(serializer.data, status=status.HTTP_200_OK)
            
        else: raise PermissionDenied({'detail':'User not authenticated.'})
    except PermissionDenied as error:
        return Response(error.args, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as error:
        return Response(error.args, status=status.HTTP_400_BAD_REQUEST)
