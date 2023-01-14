from django.urls import path, include
from . import views
urlpatterns = [
    path('profiles/', views.profiles),
    path('profiles/<int:userId>/', views.specificProfiles),
    path('profiles/<int:userId>/requests/', views.friendshipRequests),
    path('profiles/<int:userId>/requests/<int:targetUserId>/', views.specificFriendshipRequests),
    path('profiles/<int:userId>/friends/', views.friends),
    path('profiles/<int:userId>/friends/<int:targetUserId>/', views.specificFriends),
    path('profiles/<int:userId>/restricted/', views.restrictedProfiles),
    path('profiles/<int:userId>/restricted/<int:targetUserId>/', views.specificRestrictedProfiles),
    # path('profiles/<int:userId>/relations/', views.relations),
    # path('chats/', views.chats),
    # path('chats/<int:chatId>/', views.specificChats),
    # path('chats/<int:chatId>/messages/', views.messages),
    # path('chats/<int:chatId>/messages/<int:messageId>/', views.specificMessages)
]