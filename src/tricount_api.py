import json
import requests
import uuid
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

import warnings


class TricountAPI:
    def __init__(self, tricount_key: str, app_id="") -> None:
        self.base_url = "https://api.tricount.bunq.com"
        self.app_installation_id = self.__generate_installation_id(app_id)
        self.rsa_public_key_pem = self.__generate_rsa_key()
        self.tricount_key = tricount_key

        self.session = self.__create_session()

        # Cache for authentication info
        self.auth_token = None
        self.user_id = None
        self.authenticated = False

        # load the tricount data at init
        self.data = self.__requests_json()

    def __generate_installation_id(self, app_id: str) -> str:
        if app_id:
            return app_id

        app_installation_id = str(uuid.uuid4())

        # # Warning message
        # warnings.warn(
        #     f"No `app_id` provided. Generated new app ID: {app_installation_id}. For best practice, pass a consistent `app_id` when creating the TricountAPI instance.",
        #     UserWarning,
        #     stacklevel=3,
        # )

        return app_installation_id

    def __generate_rsa_key(self) -> str:
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        rsa_public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        return rsa_public_key_pem

    def __create_session(self) -> requests.Session:
        headers = {
            "User-Agent": "com.bunq.tricount.android:RELEASE:7.0.7:3174:ANDROID:13:C",
            "app-id": self.app_installation_id,
            "X-Bunq-Client-Request-Id": "049bfcdf-6ae4-4cee-af7b-45da31ea85d0",
        }

        session = requests.Session()
        session.headers.update(headers)

        return session

    def __auth_requests(self) -> dict:
        # Define the payload for the authentication request
        payload = {
            "app_installation_uuid": self.app_installation_id,
            "client_public_key": self.rsa_public_key_pem,
            "device_description": "Android",
        }

        # Make the authentication request
        response = self.session.post(
            f"{self.base_url}/v1/session-registry-installation", json=payload
        )

        return response.json()

    def __requests_json(self) -> dict:
        # Only authenticate if not already done
        if not self.authenticated:
            # Make authentification requests to have auth token and user ID
            auth_response = self.__auth_requests()

            # Debug: Print the actual response structure
            # print("Auth response structure:")
            # print(json.dumps(auth_response, indent=2, default=str))

            # Handle authentication response
            if "Response" in auth_response:
                # Successful authentication - cache the results
                self.auth_token = auth_response["Response"][1]["Token"]["token"]
                self.user_id = auth_response["Response"][3]["UserPerson"]["id"]
                self.authenticated = True

                # Update the headers to include auth token
                self.session.headers.update(
                    {"X-Bunq-Client-Authentication": self.auth_token}
                )

            elif "Error" in auth_response:
                error_msg = auth_response["Error"][0]["error_description"]
                if "Superfluous authentication" in error_msg:
                    # This shouldn't happen on first call
                    # print("Already authenticated on first call - unexpected!")
                    return {"registry": []}
                else:
                    raise ValueError(f"Authentication failed: {error_msg}")
            else:
                raise ValueError(f"Unexpected auth response format: {auth_response}")

        # Now we should have valid auth_token and user_id
        if not self.auth_token or not self.user_id:
            raise ValueError("Authentication failed: no valid token or user_id")

        # Requests tricount data
        tricount_data = self.session.get(
            f"{self.base_url}/v1/user/{self.user_id}/registry?public_identifier_token={self.tricount_key}"
        )

        return tricount_data.json()

    def update_data(self) -> None:
        """
        Requests to tricount API and update the current data
        """

        self.data = self.__requests_json()

    def get_data(self) -> dict:
        """
        Returns a dict containing the raw json data from tricount API
        """

        return self.data

    def get_users(self) -> dict:
        """
        Returns a dict with user IDs as key and user names as value
        """

        users = {}

        for user in self.data["Response"][0]["Registry"]["memberships"]:
            entry = user["RegistryMembershipNonUser"]
            id = str(entry["id"])
            name = entry["alias"]["pointer"]["name"]

            users[id] = name

        return users

    def get_expenses(self, user_id=None) -> list:
        """
        Returns a list of all expenses, can be filtered by user
        """

        expenses = []

        for expense in self.data["Response"][0]["Registry"]["all_registry_entry"]:
            entry = expense["RegistryEntry"]
            amount = float(entry["amount"]["value"])

            # skip refunds
            if entry["type_transaction"] == "BALANCE":
                continue

            # filter by user if user ID is provided
            if user_id:
                amount = None
                for allocation in entry["allocations"]:
                    if allocation["membership"]["RegistryMembershipNonUser"][
                        "id"
                    ] == int(user_id):
                        amount = float(allocation["amount"]["value"])

            if amount is not None:
                expenses.append(amount)

        return expenses
