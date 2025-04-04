from django.shortcuts import get_object_or_404
from django.utils import timezone

from api.instagram.models import Account, StatusCheck, Thread
from api.instagram.tasks import send_message


class SendContent(object):
    def __init__(self, status: str, thread: Thread) -> None:
        self.status = status
        self.instance = thread

    def change_status(self, status_level, status_name):
        self.instance.replied = True
        self.instance.replied_at = timezone.now()
        status_after_response, _ = StatusCheck.objects.get_or_create(stage=status_level, name=status_name)
        account = get_object_or_404(Account, id=self.instance.account.id)
        account.status = status_after_response
        account.save()

    def send_first_compliment(self, generated_response):
        send_message.delay(generated_response, thread_id=self.instance.thread_id)
        self.change_status(status_level=1, status_name="responded_to_first_compliment")

    def send_first_question(self, generated_response):
        """
        I hope you don't mind me also asking,\n
        I was wondering what's the gnarliest part of your barber gig?
        """
        send_message.delay(
            f"""
            {generated_response},\n
            """,
            thread_id=self.instance.thread_id,
        )
        self.change_status(status_level=2, status_name="sent_first_question")

    def send_second_question(self, generated_response):
        send_message.delay(
            f"""
            {generated_response}
            I was also thinking about asking,
            How about your clients? Is managing current ones
            more difficult than attracting new clients?
            """,
            thread_id=self.instance.thread_id,
        )
        self.change_status(status_level=2, status_name="sent_second_question")

    def send_third_question(self, generated_response):
        send_message.delay(
            f"""
            {generated_response},
            by the way could you please help me understand,
            How do you manage your calendar?
            """,
            thread_id=self.instance.thread_id,
        )
        self.change_status(status_level=2, status_name="sent_third_question")

    def send_first_needs_assessment_question(self, generated_response):
        send_message.delay(
            f"""
            {generated_response}
            besides I would like to notify you that,
            Seems like you are starting a great career, {self.instance.account.igname} 🔥
            If you don’t mind me asking... How do you market yourself? 🤔
            """,
            thread_id=self.instance.thread_id,
        )
        self.change_status(status_level=2, status_name="sent_first_needs_assessment_question")

    def send_second_needs_assesment_question(self, generated_response):
        send_message.delay(
            f"""
            {generated_response}
            I was also thinking of asking,
            Did you consider social post creator tools to make your IG account more visible? you
            have amazing potential and could easily convert your followers into clients with IG Book Button
            """,
            thread_id=self.instance.thread_id,
        )

    def send_third_needs_assessment_question(self, generated_response):
        send_message.delay(
            f"""
            {generated_response}
            by the way,
            Returning clients are critical for long-term success,
            are you able to invite back to your chair the clients who stopped booking? 🤔
            """,
            thread_id=self.instance.thread_id,
        )
        self.change_status(status_level=2, status_name="sent_third_needs_assessment_question")

    def send_follow_up_after_presentation(self, generated_response):
        send_message.delay(
            f"""
            {generated_response}
            I hope you are comfortable with me asking,
            What do you think about booksy? would you like to give it a try?
            """,
            thread_id=self.instance.thread_id,
        )
        self.change_status(status_level=2, status_name="sent_follow_up_after_presentation")

    def send_request_for_email(self, generated_response):
        send_message.delay(
            f"""
            {generated_response}
            consider also this that,
            I can quickly setup an account for you to check it out - what’s your email address?
            The one you use on IG will help with IG book button
            """,
            thread_id=self.instance.thread_id,
        )
        self.change_status(status_level=2, status_name="sent_email_first_attempt")

    def get_reason_why_uninterested(self, generated_response):
        send_message.delay(
            generated_response,
            thread_id=self.instance.thread_id,
        )
        self.change_status(status_level=3, status_name="sent_uninterest")

    def respond_to_objection(self, generated_response):
        send_message.delay(
            generated_response,
            thread_id=self.instance.thread_id,
        )
        self.change_status(status_level=3, status_name="sent_objection")
