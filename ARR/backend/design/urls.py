"""URL configuration for design app."""
from django.urls import path
from . import views

app_name = 'design'

urlpatterns = [
    path('jobs/', views.create_job, name='create_job'),
    path('jobs/<uuid:job_id>/', views.get_job, name='get_job'),
    path('jobs/<uuid:job_id>/cancel/', views.cancel_job, name='cancel_job'),
    path('jobs/<uuid:job_id>/run/', views.run_job, name='run_job'),
    path('jobs/<uuid:job_id>/stream', views.job_stream, name='job_stream'),
    path('jobs/<uuid:job_id>/results/', views.job_results, name='job_results'),
    path('jobs/<uuid:job_id>/results/<int:design_id>/', views.design_detail, name='design_detail'),
    path('jobs/<uuid:job_id>/results/<int:design_id>/evidence/', views.design_evidence, name='design_evidence'),
    path('jobs/<uuid:job_id>/results/<int:design_id>/aesthetic/', views.design_aesthetic, name='design_aesthetic'),
    path('jobs/<uuid:job_id>/validate/', views.validate_job, name='validate_job'),
    path('interactive/patch/', views.interactive_patch, name='interactive_patch'),
    path('interactive/preview/', views.interactive_preview, name='interactive_preview'),
    path('interactive/operation/', views.interactive_operation, name='interactive_operation'),
    path('maas/revision/', views.maas_conversational_revision, name='maas_conversational_revision'),
    path('maas/revision/<uuid:revision_id>/feedback/', views.maas_revision_feedback, name='maas_revision_feedback'),
    path('maas/export-scad/', views.maas_export_scad, name='maas_export_scad'),
    path('maas/legal-variants/', views.maas_legal_variants, name='maas_legal_variants'),
    path('maas/language-system/', views.maas_language_system, name='maas_language_system'),
    path('maas/outcome-graph/', views.maas_outcome_graph_slice, name='maas_outcome_graph_slice'),
    path('maas/book-assets/<int:page>/', views.maas_book_asset, name='maas_book_asset'),
    path('maas/geometry-shapes/<int:index>/', views.maas_geometry_shape_preview, name='maas_geometry_shape_preview'),
    path('maas/geometry-shapes/<int:index>/passport/', views.maas_geometry_shape_passport, name='maas_geometry_shape_passport'),
    path('maas/single-executions/', views.maas_single_execution, name='maas_single_execution'),
    path('maas/single-executions/<slug:execution_id>/preview/', views.maas_single_execution_preview, name='maas_single_execution_preview'),
    path('maas/single-executions/<slug:execution_id>/manifest/', views.maas_single_execution_manifest, name='maas_single_execution_manifest'),
    path('maas/single-executions/<slug:execution_id>/passport/', views.maas_single_execution_passport, name='maas_single_execution_passport'),
    path('maas/single-executions/<slug:execution_id>/vlm-review/', views.maas_single_execution_vlm_review, name='maas_single_execution_vlm_review'),
    path('maas/executed-masses/', views.maas_executed_masses, name='maas_executed_masses'),
    path('maas/executed-masses/<int:index>/', views.maas_executed_mass_preview, name='maas_executed_mass_preview'),
    path('maas/executed-masses/<int:index>/passport/', views.maas_executed_mass_passport, name='maas_executed_mass_passport'),
    path('maas/reference-assets/<path:asset_path>', views.maas_reference_asset, name='maas_reference_asset'),
    path('maas/aesthetic-assets/<path:asset_path>', views.maas_aesthetic_asset, name='maas_aesthetic_asset'),
    path('site-boundary/', views.site_boundary, name='site_boundary'),
    path('auto-constraints/', views.auto_constraints, name='auto_constraints'),
    path('floor-plan/', views.create_floor_plan, name='create_floor_plan'),
    path('constraints/visualize/', views.constraints_visualize, name='constraints_visualize'),
]
