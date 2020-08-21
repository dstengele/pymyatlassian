import asyncio
from pyppeteer import launch
import time
import re
import json

MA_USERNAME = "***"
MA_PASSWORD = "***"


async def main():
    browser = await launch(headless=True)
    page = await browser.newPage()
    try:
        with open("cookies.json", "r") as cookies_json:
            await page.setCookie(*json.load(cookies_json))
    except FileNotFoundError:
        pass
    await page.goto("https://my.atlassian.com")

    if re.match("https://id.atlassian.com/.*", page.url):
        username_field = await page.querySelector("#username")
        await username_field.type(MA_USERNAME)
        submit_button = await page.querySelector("#login-submit")
        await submit_button.click()
        time.sleep(1)
        password_field = await page.querySelector("#password")
        await password_field.type(MA_PASSWORD)
        await asyncio.wait(
            [submit_button.click(), page.waitForSelector("table.productTable"),]
        )

        # Cookies
        with open("cookies.json", "w") as cookie_json:
            cookies = await page.cookies()
            json.dump(cookies, cookie_json)
        pass

    license_rows = await page.querySelectorAll("tr.headingRow")
    licenses = []
    for license_row in license_rows:
        await page.evaluate(
            "(element) => element.scrollIntoViewIfNeeded()", license_row
        )
        top_id = await page.evaluate("(element) => element.id", license_row)
        await asyncio.wait(
            [license_row.click(), page.waitForSelector(f"#{top_id} + tr td#sen")]
        )
        time.sleep(1)

        license_to_add = {
            "sen": (
                await page.querySelectorEval(
                    f"#{top_id} + tr td#sen", "node => node.textContent"
                )
            ).strip(),
            "name": await license_row.querySelectorEval(
                "span.desc > strong", "node => node.textContent"
            ),
        }
        print(f"Reading SEN: {license_to_add['sen']}")

        if await page.querySelector(f"#{top_id} + tr textarea"):  # Cloud License
            license_to_add["license_string"] = await page.querySelectorEval(
                f"#{top_id} + tr textarea", "node => node.textContent"
            )
        licenses.append(license_to_add)

    await browser.close()

    print(json.dumps(licenses))


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
