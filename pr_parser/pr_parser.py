import requests
import json
import smtplib

from datetime import datetime, timedelta

from azure.cognitiveservices.language.textanalytics import TextAnalyticsClient
from msrest.authentication import CognitiveServicesCredentials


class AzureService:

    def __init__(self):
        config_path = 'azure_config.json'
        with open(config_path) as json_file:
            data = json.load(json_file)
            self.endpoint_var_name = data["endpoint"]
            self.key_var_name = data["key"]

            self.client = self.authenticate_client()

    def authenticate_client(self):
        credentials = CognitiveServicesCredentials(self.key_var_name)
        text_analytics_client = TextAnalyticsClient(
            endpoint=self.endpoint_var_name, credentials=credentials)
        return text_analytics_client

    def get_sentiment_for(self, comments: [str]) -> float:
        try:
            documents = []
            for i, comment in enumerate(comments):
                documents.append({"id": i,
                                  "language": "en",
                                  "text": comment}
                                 )
            print(documents)
            response = self.client.sentiment(documents=documents)
            total_score = 0.0
            for document in response.documents:
                total_score += document.score
                print("{:.2f}".format(document.score))

            return total_score/len(documents)

        except Exception as err:
            print("Encountered exception. {}".format(err), err)
        pass


class RecommendationDispatcher:
    host: str
    port: int
    user_email: str
    password: str
    supervisor_email: str

    def __init__(self):
        with open('email_config') as json_file:
            cfg = json.load(json_file)
            host = cfg["host"]
            port = cfg["port"]
            user_email = cfg["email"]
            password = cfg["password"]

        with open('../userType.json') as json_file:
            data = json.load(json_file)
            supervisor_email = data["supervisor_email"]

    def send_recommendation_mail(self, message):
        server = smtplib.SMTP_SSL(self.host, self.port)
        server.login(user=self.user_email, password=self.password)
        server.sendmail(
            from_addr=self.user_email,
            to_addrs=self.supervisor_email,
            msg=message
        )
        server.quit()


class FeedbackGenerator:
    POLARITY_THRESHOLD = 0.5

    def __init__(self):
        user_details_path = '../userType.json'
        with open(user_details_path) as json_file:
            data = json.load(json_file)
            self.personality_type = data["type"]
            self.github_id = data["github_id"]

        self.azure_service = AzureService()

    def get_recommended_feedback(self, personality_type, sentiment) -> str:
        feedback = ""
        with open('../emailFeedbackRecommendations.json') as json_file:
            data = json.load(json_file)
            if personality_type == 1:
                user_type = data["type1"]
                # positive
                if sentiment >= self.POLARITY_THRESHOLD:
                    feedback = user_type["pos"]
                # negative
                else:
                    feedback = user_type["neg"]
            if personality_type == 2:
                user_type = data["type2"]
                # positive
                if sentiment >= self.POLARITY_THRESHOLD:
                    feedback = user_type["pos"]
                # negative
                else:
                    feedback = user_type["neg"]
            if personality_type == 3:
                user_type = data["type3"]
                # positive
                if sentiment >= self.POLARITY_THRESHOLD:
                    feedback = user_type["pos"]
                # negative
                else:
                    feedback = user_type["neg"]
        return feedback

    def send_recommended_feedback(self, sentiment):
        message = self.get_recommended_feedback(personality_type=self.personality_type, sentiment=sentiment)
        RecommendationDispatcher().send_recommendation_mail(message=message)

    def run(self):

        base_url = 'https://api.github.com'
        mock_repo_url = "/repos/GilgusMaximus/Kind-Feedback"
        mozilla_url = "/repos/mozilla-mobile/firefox-ios"
        mozilla_closed_issue_comments = '/issues/5788/comments'

        # determine closed PRs
        try:
            closed_prs_response = requests.get(base_url + mock_repo_url + '/pulls', params=dict(state="closed"))
            print(base_url + mozilla_url + '/pulls')
            print(closed_prs_response)

            for closed_pr in closed_prs_response.json():

                # only closed today
                print(closed_pr)
                unformated_closing_date = closed_pr["closed_at"]
                closing_date = datetime.strptime(unformated_closing_date, "%Y-%m-%dT%H:%M:%SZ").date()

                # only by submitter
                submitter_id = closed_pr["user"]["login"]

                if closing_date == (datetime.now() - timedelta(1)).date() and submitter_id == self.github_id:

                    # get comments of reviewers (not submitter) of closed pr
                    issue_number = str(closed_pr["number"])
                    pr_comments_response = requests.get(base_url + mock_repo_url + '/issues' + '/' + issue_number + '/comments')

                    comments = []
                    sentiment = 0.0
                    for comment in pr_comments_response.json():
                        # filter comments by submitter
                        if comment["user"]["login"] != self.github_id:
                            body = comment["body"]
                            comments.append(body)

                    sentiment = self.azure_service.get_sentiment_for(comments)

                    # abschicken
                    self.send_recommended_feedback(sentiment=sentiment)

        except Exception as err:
            print(err)


if __name__ == '__main__':
    FeedbackGenerator().run()

