from django.urls import path

from .views import (
    OrganizationDetailView,
    OrganizationListCreateView,
    OrganizationMemberDetailView,
    OrganizationMemberListCreateView,
)

urlpatterns = [
    path("", OrganizationListCreateView.as_view(), name="organization-list-create"),
    path("<uuid:id>", OrganizationDetailView.as_view(), name="organization-detail"),
    path(
        "<uuid:id>/members",
        OrganizationMemberListCreateView.as_view(),
        name="organization-member-list-create",
    ),
    path(
        "<uuid:id>/members/<uuid:member_id>",
        OrganizationMemberDetailView.as_view(),
        name="organization-member-detail",
    ),
]
