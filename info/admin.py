from django.contrib import admin

# Register your models here.
from info.models import Info


class InfoAdmin(admin.ModelAdmin):
    model = Info
    list_display = ['resident_code',
                    'name',
                    'acquisi_date',
                    'disqual_date',
                    'start_workyear',

                    'workdate_1',
                    'workdate_2',
                    'workdate_3',
                    'workdate_4',
                    'workdate_5',

                    'total_workdate',
                    'young_workdate_1',
                    'young_workdate_2',
                    'young_workdate_3',
                    'young_workdate_4',
                    'young_workdate_5',
                    'total_young_workdate',

                    'executive',
                    'contract_worker',
                    'army',
                    'elder']


admin.site.register(Info, InfoAdmin)
