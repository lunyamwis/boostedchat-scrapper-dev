import os
import json
from pathlib import Path

from django.core.files import File

from api.authentication.models import User
from api.instagram.models import Account, OutSourced, StatusCheck, ExperimentStatus
from api.sales_rep.models import SalesRep


def init_status_check():
    # stage 1
    sent_first_compliment = StatusCheck()
    sent_first_compliment.stage = 1
    sent_first_compliment.name = "sent_first_compliment"
    sent_first_compliment.save()

    sent_compliment = StatusCheck()
    sent_compliment.stage = 1
    sent_compliment.name = "sent_compliment"
    sent_compliment.save()

    # stage 2
    sent_first_question = StatusCheck()
    sent_first_question.stage = 2
    sent_first_question.name = "sent_first_question"
    sent_first_question.save()

    confirmed_problem = StatusCheck()
    confirmed_problem.stage = 2
    confirmed_problem.name = "confirmed_problem"
    confirmed_problem.save()

    overcome_objections = StatusCheck()
    overcome_objections.stage = 2
    overcome_objections.name = "overcome_objections"
    overcome_objections.save()

    # stage 3
    overcome = StatusCheck()
    overcome.stage = 3
    overcome.name = "overcome"
    overcome.save()

    deferred = StatusCheck()
    deferred.stage = 3
    deferred.name = "deferred"
    deferred.save()

    # stage 4
    activation = StatusCheck()
    activation.stage = 4
    activation.name = "activation"
    activation.save()
    
def init_experiment_status():
    # stage 1
    set_draft = ExperimentStatus()
    set_draft.name = 'draft'
    set_draft.description = "draft"
    set_draft.save()


def init_db():
    pass