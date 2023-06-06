# -*- coding: utf-8 -*-

from django.db import models

# Create your models here.


class UserDialogPosition(models.Model):
    conversation_id = models.CharField(max_length=200, blank=False, verbose_name="Conversation ID",
                                       default="0")
    type = models.CharField(max_length=30, choices=(("question", "question"),
                                                    ("answer", "answer"),
                                                    ("additional_answer", "additional answer"),
                                                    ("result_evaluation", "result evaluation")),
                            verbose_name="Messege type", blank=False, default="question")
    content = models.TextField(blank=True, verbose_name="Messege content", null=True)
    additional_info =models.TextField(blank=True, verbose_name="Additional information", null=True)
    date_time = models.DateTimeField(auto_now_add=True, verbose_name="Time", blank=False)

    class Meta:
        db_table = 'DialogPositions'
        verbose_name = 'Dialog messages'













