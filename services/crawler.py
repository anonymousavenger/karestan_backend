import os
from time import sleep
from random import randint
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json


class Crawler:
    __driver: Optional[webdriver.Chrome] = None
    retries = 0

    @classmethod
    def setup_webdriver(cls, headless=True):
        options = Options()
        options.headless = headless
        options.add_argument("--disable-blink-features=AutomationControlled")
        cls.__driver = webdriver.Chrome(executable_path="resources"
                                                        "/chromedriver-92", options=options)

    @classmethod
    def run_webdriver_on_site(cls, site='https://google.com'):
        cls.__driver.get(site)
        sleep(1)

    @classmethod
    def load(cls, url="http://webcache.googleusercontent.com/search?q=cache:https://jobguy.work/interview/284",
             headless=False):
        if cls.__driver is None:
            cls.setup_webdriver(headless=headless)
        cls.__driver.get(url)
        return cls.__driver

    @classmethod
    def is_detected(cls):
        source: str = cls.__driver.page_source
        if source.find("Our systems have detected") == -1:
            return False
        else:
            return True

    @classmethod
    def shutdown(cls):
        if cls.__driver is not None:
            cls.__driver.service.stop()
            cls.__driver.quit()
            try:
                pid = True
                while pid:
                    pid = os.waitpid(-1, os.WNOHANG)
                    print("Reaped child: %s" % str(pid))

                    # Wonka's Solution to avoid infinite loop cause pid value -> (0, 0)
                    try:
                        if pid[0] == 0:
                            pid = False
                    except:
                        print("Problem with shutting down the driver")
                    # ---- ----

            except ChildProcessError:
                pass
            cls.__driver = None
        else:
            raise

    @classmethod
    def get_driver(cls):
        if cls.__driver is not None:
            return cls.__driver
        else:
            raise Exception("Driver is not initialized")

    @classmethod
    def has_captcha(cls):
        try:
            Crawler.__driver.find_element_by_id("captcha-form")
            return True
        except:
            return False

    @classmethod
    def run(cls, start, end=2800):
        # start from 502
        failed = []
        i = start - 1
        end += 1
        while i < end:
            i += 1
            url = "http://webcache.googleusercontent.com/search?q=cache:https://jobguy.work/interview/" + str(i)
            cls.__driver.get(url)
            try:
                cls.__driver.find_element_by_class_name("nuxt-link-active")
                with open(f"interviews/{i}.html", "a+") as h:
                    h.write(cls.__driver.page_source)
            except:
                if cls.is_detected():
                    print(f"detected! -> {i}")
                    if cls.has_captcha():
                        correct_input = False
                        x = 'n'
                        while not correct_input:
                            x = input("are we good? (y/n) ")
                            correct_input = x in ['y', 'n']
                        if x == 'y':
                            i -= 1
                            continue
                        else:
                            print(f"Stopped at: {i}")
                            break
                    else:
                        if cls.retries > 20:
                            print("Maximum retires reached for loading recaptcha. Exiting")
                            break
                        else:
                            cls.retries += 1
                            print(f"Retrying... attempt {cls.retries}")
                            sleep(cls.retries * 10)
                            i -= 1
                            continue
                else:
                    print(f"failed: {i}")
                    failed.append(i)
                    continue
            finally:
                s = randint(1, 1000) / 1000 * 2
                sleep(s)
        cls.__driver.close()
