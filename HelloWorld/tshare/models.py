from django.db import models

# Create your models here.
class StatisticTradeData(models.Model):
    index = models.BigIntegerField(blank=True, null=True)
    code = models.TextField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    i_date = models.DateField(blank=True, null=True)
    o_date = models.DateField(blank=True, null=True)
    i_total = models.BigIntegerField(blank=True, null=True)
    o_total = models.BigIntegerField(blank=True, null=True)
    amount = models.BigIntegerField(blank=True, null=True)
    time = models.IntegerField(blank=True, null=True)
    earning = models.BigIntegerField(blank=True, null=True)
    pct = models.FloatField(blank=True, null=True)
    id = models.BigIntegerField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'statistic_trade_data'

class OriginalTradeData(models.Model):
    index = models.BigIntegerField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    code = models.TextField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    operation = models.TextField(blank=True, null=True)
    amount = models.IntegerField(blank=True, null=True)
    price = models.FloatField(blank=True, null=True)
    sum = models.FloatField(blank=True, null=True)
    getsum = models.FloatField(blank=True, null=True)
    getamount = models.FloatField(blank=True, null=True)
    id = models.BigIntegerField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'original_trade_data'
		
# from tshare.models import KQfq002242 as kdate
# kdata._meta.db_table= 。。。。。 在外部修改数据库
		

		
		
class K_days(models.Model):
    index = models.BigIntegerField(blank=True, null=True)
    date = models.TextField(blank=True, null=True)
    open = models.FloatField(blank=True, null=True)
    close = models.FloatField(blank=True, null=True)
    high = models.FloatField(blank=True, null=True)
    low = models.FloatField(blank=True, null=True)
    volume = models.FloatField(blank=True, null=True)
    code = models.TextField(blank=True, null=True)
    id = models.BigIntegerField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'k_bfq'
		
	
	