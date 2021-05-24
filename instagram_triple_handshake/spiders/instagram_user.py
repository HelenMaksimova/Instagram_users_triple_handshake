import scrapy
import json
from ..loaders import InstFollowerLoader, InstFollowingLoader


class InstagramUserSpider(scrapy.Spider):
    name = 'instagram_user'
    allowed_domains = ['www.instagram.com', 'i.instagram.com']
    start_urls = ['https://www.instagram.com/']
    _login_url = "https://www.instagram.com/accounts/login/ajax/"
    _api_headers = {
        'followers': {
            'X-IG-App-ID': '936619743392459',
            'X-IG-WWW-Claim': 'hmac.AR33ssnHA9SsvJK9oOXcF6zebs3Rw39b3N4wW'
        },
        'following':
            {'X-IG-App-ID': '936619743392459',
             'X-IG-WWW-Claim': 'hmac.AR33ssnHA9SsvJK9oOXcF6zebs3Rw39b3N4wWW3JU7Or1Xsy'
             }
    }

    def __init__(self, login, password, user_names, coil, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.login = login
        self.password = password
        self.user_names = user_names
        self.coil = coil
        self.auth_flag = False

    def authorization(self, response):
        js_data = js_data_extract(response)
        self.auth_flag = True
        yield scrapy.FormRequest(
            self._login_url,
            method="POST",
            callback=self.parse,
            formdata={"username": self.login, "enc_password": self.password},
            headers={"X-CSRFToken": js_data["config"]["csrf_token"]},
        )

    def parse(self, response, *args, **kwargs):
        if not self.auth_flag:
            yield from self.authorization(response)
        else:
            for name in self.user_names:
                url = f"/{name}/"
                yield response.follow(url, callback=self.user_page_parse, cb_kwargs={'username': name})

    def user_page_parse(self, response, username):
        user = InstUser(response)
        user_item = user.get_item()
        yield response.follow(user.get_api_url(user_item['user_id'], 'followers'),
                              callback=self.follow_parse,
                              headers=self._api_headers['followers'],
                              cb_kwargs={'user_id': user_item['user_id'],
                                         'parent': username,
                                         'api_type': 'followers',
                                         'loader_class': InstFollowerLoader}
                              )
        yield response.follow(user.get_api_url(user_item['user_id'], 'following'),
                              callback=self.follow_parse,
                              headers=self._api_headers['following'],
                              cb_kwargs={'user_id': user_item['user_id'],
                                         'parent': username,
                                         'api_type': 'following',
                                         'loader_class': InstFollowingLoader}
                              )

    def follow_parse(self, response, user_id, parent, api_type, loader_class):
        next_max_id = response.json().get('next_max_id')
        followers = InstUser(response, next_max_id)
        for follower in followers.get_item_array():
            yield from self.load_item({'username': follower, 'parent': parent, 'user_type': api_type}, loader_class)
        if next_max_id is not None:
            yield response.follow(followers.get_api_url(user_id, api_type),
                                  callback=self.follow_parse,
                                  headers=self._api_headers[api_type],
                                  cb_kwargs={'user_id': user_id,
                                             'parent': parent,
                                             'api_type': api_type,
                                             'loader_class': loader_class}
                                  )

    @staticmethod
    def load_item(data, loader_class):
        loader = loader_class()
        for field_name, value in data.items():
            loader.add_value(field_name, value)
        yield loader.load_item()


class InstUser:

    api_url = 'https://i.instagram.com/api/v1/friendships/'

    def __init__(self, response, max_id=0):
        self.response = response
        self.count = 1000
        self.max_id = max_id

    def get_item(self):
        user_data = self.get_user_data()
        return {'user_id': user_data['id'], 'username': user_data['username']}

    def get_item_array(self):
        users_array = self._get_users_array()
        item_array = [user['username'] for user in users_array]
        return item_array

    def get_next_max_id(self):
        pass

    def get_api_url(self, user_id, api_type):
        if int(self.max_id) > 0:
            return f'{self.api_url}{user_id}/{api_type}/' \
                   f'?count={self.count}&max_id={self.max_id}&search_surface=follow_list_page'
        return f'{self.api_url}{user_id}/{api_type}/' \
               f'?count={self.count}&search_surface=follow_list_page'

    def get_user_data(self):
        return js_data_extract(self.response)['entry_data']['ProfilePage'][0]['graphql']['user']

    def _get_users_array(self):
        return self.response.json()['users']


def js_data_extract(response):
    script = response.xpath(
        "//script[contains(text(), 'window._sharedData = ')]/text()"
    ).extract_first()
    return json.loads(script.replace("window._sharedData = ", "")[:-1])
