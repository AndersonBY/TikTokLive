from httpx import Response

from TikTokLive.client.web.routes.fetch_room_id_html import FailedParseRoomIdError
from TikTokLive.client.web.web_base import ClientRoute, TikTokHTTPClient
from TikTokLive.client.web.web_settings import WebDefaults


class UserNotFound(RuntimeError):
    """
    Thrown when the request to check if a user is live fails because a user has no
    livestream account (e.g. <1000 followers)

    """

    def __init__(self, unique_id: str, *args):
        self.unique_id: str = unique_id
        super().__init__(*args)


class RoomIdAPIRoute(ClientRoute):
    """
    Route to retrieve the room ID for a user

    """

    async def __call__(self, unique_id: str) -> str:
        """
        Fetch the Room ID for a given unique_id from the TikTok API

        :param unique_id: The user's uniqueId
        :return: The room ID string

        """

        # Get their livestream room ID from the api
        room_data: dict = await self.fetch_user_room_data(
            web=self._web,
            unique_id=unique_id
        )

        # Parse & update the web client
        room_id = self._web.params["room_id"] = self.parse_room_id(room_data)
        return room_id

    @classmethod
    async def fetch_user_room_data(cls, web: TikTokHTTPClient, unique_id: str) -> dict:
        """
        Fetch user room from the API (not the same as room info)

        :param web: The TikTokHTTPClient client to use
        :param unique_id: The user to check
        :return: The user's room info

        """

        response: Response = await web.get_response(
            url=WebDefaults.tiktok_app_url + f"/api-live/user/room/",
            extra_params=(
                {
                    "uniqueId": unique_id,
                    "sourceType": 54
                }
            )
        )

        response_json: dict = response.json()

        # Invalid user
        if response_json["message"] == "user_not_found":
            raise UserNotFound(
                unique_id,
                (
                    f"The requested user '{unique_id}' is not capable of going LIVE on TikTok, "
                    "or has never gone live on TikTok, or does not exist."
                )
            )

        return response_json

    @classmethod
    def parse_room_id(cls, data: dict) -> str:
        """
        Parse the room ID from livestream API response

        :param data: The data to parse
        :return: The user's room id
        :raises: UserOfflineError if the user is offline
        :raises: FailedParseRoomIdError if the user data does not exist

        """

        try:
            return data['data']['user']['roomId']
        except KeyError:
            raise FailedParseRoomIdError("That user can't stream, or you might be blocked by TikTok.")
