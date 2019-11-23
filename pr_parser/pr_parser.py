import requests
import json
import os
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

    def get_sentiment_for(self, comments: [str]):
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

            print('Total:', total_score/len(documents))

        except Exception as err:
            print("Encountered exception. {}".format(err), err)
        pass


class FeedbackGenerator:
    def get_recommended_feedback(self) -> str:
        return ""

    def send_recommended_feedback(self):
        pass

    def setup(self):
        user_details_path = '../userType.json'
        with open(user_details_path) as json_file:
            data = json.load(json_file)
            self.personality_type = data["type"]
            self.github_id = data["github_id"]

        self.azure_service = AzureService()


    def __init__(self):
        pass

    def run(self):
        personality_type = ""
        github_id = ""
        self.setup()

        base_url = 'https://api.github.com'
        mock_repo_url = "/repos/GilgusMaximus/Kind-Feedback"
        mozilla_url = "/repos/mozilla-mobile/firefox-ios"
        mozilla_closed_issue_comments = '/issues/5788/comments'

        # determine closed PRs
        try:
            #closed_prs_response = requests.get(base_url + mock_repo_url + '/pulls', params=dict(state="closed"))
            closed_prs_response = requests.get(base_url + mozilla_url + '/pulls', params=dict(state="closed"))
            print(base_url + mozilla_url + '/pulls')
            print(closed_prs_response)


            for closed_pr in closed_prs_response.json():

                # only closed today
                print(closed_pr)
                unformated_closing_date = closed_pr["closed_at"]
                closing_date = datetime.strptime(unformated_closing_date, "%Y-%m-%dT%H:%M:%SZ").date()

                # only by submitter
                submitter_id = closed_pr["user"]["login"]

                if closing_date == (datetime.now() - timedelta(1)).date() and submitter_id == github_id:

                    # get comments of reviewers (not submitter) of closed pr
                    issue_number = str(closed_pr["number"])
                    #pr_comments_response = requests.get(base_url + mock_repo_url + '/issues' + '/' + issue_number + '/comments')
                    pr_comments_response = requests.get(base_url + mozilla_url + mozilla_closed_issue_comments)

                    comments = []
                    for comment in pr_comments_response.json():
                        # filter comments by submitter
                        if comment["user"]["login"] != github_id:
                            body = comment["body"]
                            comments.append(body)
                            self.azure_service.get_sentiment_for(comments)

                    recommended_feedback = self.get_recommended_feedback()

        except Exception as err:
            print(err)

if __name__ == '__main__':
    FeedbackGenerator.run(FeedbackGenerator())
