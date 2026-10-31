from django.urls import path

from apps.library import reflection_views, views

urlpatterns = [
    path("carti/", views.catalog, name="catalog"),
    path("carti/<uuid:book>/", views.book_detail, name="book_detail"),
    path("carti/<uuid:book>/adauga/", views.add_to_shelf, name="add_to_shelf"),
    path("raft/", views.my_shelf, name="my_shelf"),
    path("raft/<uuid:entry>/", views.shelf_entry, name="shelf_entry"),
    path("raft/<uuid:entry>/progres/", views.record_progress, name="record_progress"),
    path("raft/<uuid:entry>/terminat/", views.finish_book, name="finish_book"),
    path("raft/<uuid:entry>/evaluare/", views.rate_book, name="rate_book"),
    path("raft/<uuid:entry>/ganduri/", reflection_views.book_reflection, name="book_reflection"),
    path("raft/<uuid:entry>/ganduri/set/", reflection_views.start_reflection, name="start_reflection"),
    path("raft/<uuid:entry>/ganduri/salveaza/", reflection_views.save_reflection, name="save_reflection"),
]
