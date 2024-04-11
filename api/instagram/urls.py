from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'scores', views.ScoreViewSet)
router.register(r'qualification_algorithms', views.QualificationAlgorithmViewSet)
router.register(r'schedulers', views.SchedulerViewSet)
router.register(r'lead_sources', views.LeadSourceViewSet)
router.register(r'simplehttpoperator',views.SimpleHttpOperatorViewSet)
router.register(r'workflows',views.WorkflowViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('scrapFollowers/', views.ScrapFollowers.as_view()),
    path('scrapGmaps/', views.ScrapGmaps.as_view()),
    path('scrapTheCut/', views.ScrapTheCut.as_view()),
    path('scrapStyleseat/',views.ScrapStyleseat.as_view()),
    path('scrapAPI/', views.ScrapAPI.as_view()),
    path('scrapURL/', views.ScrapURL.as_view()),
    path('scrapMindBodyOnline/', views.ScrapMindBodyOnline.as_view()),
    path('scrapSiteMaps/', views.ScrapSitemaps.as_view()),
    path('scrapUsers/', views.ScrapUsers.as_view()),
    path('scrapInfo/', views.ScrapInfo.as_view()),
    path('insertAndEnrich/', views.InsertAndEnrich.as_view()),
]

