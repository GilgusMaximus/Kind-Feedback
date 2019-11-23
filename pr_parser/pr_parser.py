import requests
import json
import os
from datetime import datetime, timedelta

from azure.cognitiveservices.language.textanalytics import TextAnalyticsClient
from msrest.authentication import CognitiveServicesCredentials


class AzureService:

    def __init__(self):
        config_path = 'azure_config.json'
        print(os.environ)
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
            for comment, i in enumerate(comments):
                documents.append({"id": i,
                                  "language": "en",
                                  "text": comment}
                                 )

            response = self.client.sentiment(documents=documents)
            for document in response.documents:
                return document.score
                # print("{:.2f}".format(document.score))

        except Exception as err:
            print("Encountered exception. {}".format(err), err)
        pass


def get_recommended_feedback() -> str:
    return ""


def send_recommended_feedback():
    pass


def main():
    global personality_type, github_id

    user_details_path = '../userType.json'
    with open(user_details_path) as json_file:
        data = json.load(json_file)
        personality_type = data["type"]
        github_id = data["github_id"]

    azure_service = AzureService()

    base_url = 'https://api.github.com'
    mock_repo_url = "/repos/GilgusMaximus/Kind-Feedback"
    mozilla_issue_url = "/repos/mozilla-mobile/firefox-ios"

    # determine closed PRs
    closed_prs_response = requests.get(base_url + mock_repo_url + '/pulls', params=dict(state="closed"))

    for closed_pr in closed_prs_response.json():

        # only closed today
        print(closed_pr)
        unformated_closing_date = closed_pr["closed_at"]
        closing_date = datetime.strptime(unformated_closing_date, "%Y-%m-%dT%H:%M:%SZ").date()

        # only by submitter
        submitter_id = closed_pr["user"]["login"]
        print(closing_date)

        if closing_date == datetime.now().date() and submitter_id == github_id:

            # get comments of reviewers (not submitter) of closed pr
            issue_number = closed_pr["number"]
            pr_comments_response = requests.get(base_url + mock_repo_url + '/issues' + '/' + issue_number + '/comments')

            comments = []
            for comment in pr_comments_response.json():
                # filter comments by submitter
                if comment["user"]["login"] != github_id:
                    body = comment["body"]
                    comments.append(body)

                azure_service.get_sentiment_for(comments)
            recommended_feedback = get_recommended_feedback()

    # response = requests.get(base_url + mock_repo_url + '/issues' + '/' + issue_number + '/comments')


if __name__ == '__main__':
    main()
