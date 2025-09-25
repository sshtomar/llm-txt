"""GitHub device flow authentication."""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Optional
import aiohttp


class GitHubAuth:
    """Handle GitHub device flow authentication."""

    def __init__(self):
        self.token_path = Path.home() / '.llmxt' / 'github.token'
        self.token_path.parent.mkdir(parents=True, exist_ok=True)

    async def device_flow_login(self, client_id: str) -> bool:
        """
        Perform GitHub device flow authentication.

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Request device code
            device_code_response = await self._request_device_code(client_id)

            if not device_code_response:
                return False

            verification_uri = device_code_response['verification_uri']
            user_code = device_code_response['user_code']
            device_code = device_code_response['device_code']
            interval = device_code_response.get('interval', 5)

            # Display instructions
            print(f"\nPlease visit: {verification_uri}")
            print(f"and enter code: {user_code}\n")

            # Poll for token
            token = await self._poll_for_token(client_id, device_code, interval)

            if token:
                self._save_token(token)
                return True

            return False

        except Exception as e:
            print(f"Authentication error: {e}")
            return False

    async def _request_device_code(self, client_id: str) -> Optional[Dict]:
        """Request device and user codes from GitHub."""
        url = 'https://github.com/login/device/code'
        headers = {'Accept': 'application/json'}
        data = {'client_id': client_id}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, data=data, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        print(f"Failed to get device code: {error_text}")
                        return None
            except aiohttp.ClientError as e:
                print(f"Network error: {e}")
                return None

    async def _poll_for_token(
        self,
        client_id: str,
        device_code: str,
        interval: int
    ) -> Optional[str]:
        """Poll GitHub for the access token."""
        url = 'https://github.com/login/oauth/access_token'
        headers = {'Accept': 'application/json'}

        async with aiohttp.ClientSession() as session:
            while True:
                data = {
                    'client_id': client_id,
                    'device_code': device_code,
                    'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
                }

                try:
                    async with session.post(url, data=data, headers=headers) as response:
                        result = await response.json()

                        if 'access_token' in result:
                            return result['access_token']

                        error = result.get('error')

                        if error == 'authorization_pending':
                            # User hasn't authorized yet, keep polling
                            await asyncio.sleep(interval)
                            continue
                        elif error == 'slow_down':
                            # Polling too fast, increase interval
                            interval += 5
                            await asyncio.sleep(interval)
                            continue
                        elif error == 'expired_token':
                            print("Device code expired. Please try again.")
                            return None
                        elif error == 'access_denied':
                            print("Access denied by user.")
                            return None
                        else:
                            print(f"Error: {error}")
                            return None

                except aiohttp.ClientError as e:
                    print(f"Network error: {e}")
                    await asyncio.sleep(interval)
                    continue

    def _save_token(self, token: str):
        """Save the token to a secure location."""
        self.token_path.write_text(token)
        # Set file permissions to 600 (read/write for owner only)
        self.token_path.chmod(0o600)

    def get_token(self) -> Optional[str]:
        """Retrieve the stored token."""
        if self.token_path.exists():
            try:
                return self.token_path.read_text().strip()
            except Exception:
                return None
        return None

    async def get_user(self) -> Optional[Dict]:
        """Get authenticated user information."""
        token = self.get_token()

        if not token:
            return None

        url = 'https://api.github.com/user'
        headers = {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {token}'
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 401:
                        print("Invalid or expired token")
                        return None
                    else:
                        return None
            except aiohttp.ClientError:
                return None

    def logout(self):
        """Remove stored token."""
        if self.token_path.exists():
            self.token_path.unlink()
            print("Logged out successfully")