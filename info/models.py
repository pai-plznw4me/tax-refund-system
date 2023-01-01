from django.db import models


# Create your models here.

class Info(models.Model):
    filename = models.CharField(max_length=200)  # 상실명부파일이름
    resident_code = models.CharField(max_length=13)
    name = models.CharField(max_length=10)
    acquisi_date = models.DateField()  # 자격 취득일
    disqual_date = models.DateField(null=True, blank=True)  # 자격 상실일
    start_workyear = models.IntegerField()  # 기준 근무일

    workdate_1 = models.IntegerField()
    workdate_2 = models.IntegerField()
    workdate_3 = models.IntegerField()
    workdate_4 = models.IntegerField()
    workdate_5 = models.IntegerField()
    total_workdate = models.IntegerField()

    young_workdate_1 = models.IntegerField(null=True)
    young_workdate_2 = models.IntegerField(null=True)
    young_workdate_3 = models.IntegerField(null=True)
    young_workdate_4 = models.IntegerField(null=True)
    young_workdate_5 = models.IntegerField(null=True)
    total_young_workdate = models.IntegerField(null=True)

    executive = models.BooleanField(default=False)  # 임원 여부
    contract_worker = models.BooleanField(default=False)  # 1년 계약직 여부
    army = models.BooleanField(default=False)  # 군대 여부
    elder = models.BooleanField(default=False)  # 노인 여부
    Disabled = models.BooleanField(default=False)
