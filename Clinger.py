import tty
import sys
import time
import signal
import getpass
from bs4 import BeautifulSoup
from selenium import webdriver
from builtins import print
import selenium.common.exceptions as SE
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


class link_to_be_like(object):
    """An expectation for checking that a page has a particular web address.
    expected_link - used to match address
    returns True once it has the particular web address.
    """
    def __init__(self, expected_link):
        self.expected_link = expected_link

    def __call__(self, driver):
        if self.expected_link in driver.current_url.strip():
            return True
        else:
            return False


def getch():
    try:
        import termios
    except ImportError:
        # Non-POSIX. Return msvcrt's (Windows') getch.
        import msvcrt
        return msvcrt.getch

        # POSIX system. Create and return a getch that manipulates the tty.
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def interrupted(signum, frame):
    raise Exception


signal.signal(signal.SIGALRM, interrupted)


def input_with_timeout(msg, timeout):
    try:
        signal.alarm(timeout)
        print(msg, end="\r")
        foo = getch()
        signal.alarm(0)
        return foo
    except:
        return


class Clinger:
    def __init__(self, driver):
        self.driver = driver
        self.me = ''
        print("Opening up Messenger...")
        self.driver.get("https://en-gb.facebook.com/login.php?next=https://en-gb.facebook.com/messages/t")
        self.driver.maximize_window()
        self.login()

    def login(self):
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "email")))
        self.driver.find_element_by_id("email").send_keys(input("Enter your Facebook ID: "))
        self.driver.find_element_by_name("pass").send_keys(getpass.getpass("Enter Your Password: "))
        print("Logging In...")
        self.driver.find_element_by_name("pass").send_keys(Keys.ENTER)

        # check if logged in successfully
        try:
            WebDriverWait(self.driver, 20).until(
                link_to_be_like("https://www.facebook.com/messages/t/")
            )
            self.me = self.driver.find_element(By.XPATH, "//span[@class=\"_1vp5\"]").text.strip()
            login_check = True
        except SE.TimeoutException:
            login_check = False

        if login_check:
            print("You're Logged in %s. Enjoy!..." % self.me)
            return self.messenger()
        else:
            print("The email address or phone number that you've entered doesn't match any account. ")
            return self.login()
        # if "" in driver.page_source:
        #     print("The email address or phone number that you've entered doesn't match any account. ")
        #     return self.login()
        # Remove annoying pop up
        # try:
        #     WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT,
        #                                                                      "Not Now"))).click()
        # except SE.TimeoutException:
        #     pass

    def messenger(self):

        if self.selector():
            self.do_chat()

    def selector(self):
        search_box = self.driver.find_element_by_xpath('//input[@placeholder="Search Messenger"]')
        # chatterers = []
        tries = 3
        chat_finder = ''
        while tries > 0:
            try:
                chat_finder = int(input("1. Contacts\n2. Groups\n3. Search: "))
                if not 0 < chat_finder < 4:
                    raise ValueError
            except ValueError:
                print("Invalid Input. Please provide a valid input (a number 1,2 or 3)")
                tries -= 1
            else:
                break

        if tries == 0 or chat_finder == '':
            print("You exceeded maximum tries.")
            return False
        else:
            tries = 3

        if chat_finder == 3:
            search_keys = input("Enter the keyword to be searched: ")
            search_box.click()
            search_box.send_keys(search_keys)

            # Search for 4 seconds
            time_out = 10
            search_exist = 5
            while time_out > 0 and search_exist > 0:
                if "Searching..." in self.driver.page_source:
                    search_exist += 1
                else:
                    search_exist -= 1
                time.sleep(.25)
                time_out -= 1
                print("Searching...", end="\r")
            print("Search Complete!")

        try:
            search_box.click()
            chatterers = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//ul[@role=\"listbox\"]")))
        except SE.TimeoutException:
            print("Not Found chatterers! Timeout!")
            return False

        if chat_finder == 3:
            people = []
            contacts = ["<Contacts>"]
            groups = ["<Groups>"]
            others = ["<Others>"]
            for i in self.driver.find_elements_by_xpath("//div[@class=\"_29hk\"]")[1:]:
                if "Contacts" in i.text.split()[0]:
                    contacts.extend(i.find_elements_by_tag_name("li"))
                elif "Group" in i.text.split()[0]:
                    groups.extend(i.find_elements_by_tag_name("li"))
                else:
                    others.extend(i.find_elements_by_tag_name("li"))

            people.extend(contacts)
            people.extend(groups)
            people.extend(others)

            offset = 0
            for i in enumerate(people[:]):
                if i[1] == "<Contacts>" or i[1] == '<Groups>' or i[1] == '<Others>':
                    print("\n"+i[1])
                    people.remove(i[1])
                    offset += 1
                else:
                    end = "\n" if i[0] != 0 and (i[0] + 1 - offset) % 3 == 0 else "\t"
                    print("{:3d}. {:<25.25}".format(i[0] + 1 - offset, i[1].text.replace("\n", "-")), end=end)
            people = list(enumerate(people))

        else:
            people = list(enumerate(chatterers[chat_finder - 1].find_elements_by_tag_name("li")))
            for i in people:
                end = "\n" if i != 0 and i[0] % 3 == 0 else "\t"
                print("{:3d}. {:<25.25}".format(i[0] + 1, i[1].text.strip()), end=end)

        while tries > 0:
            try:
                person = int(input("\nWhom do you want to talk with?[1-%d](-1 to go back to Menu): " % len(people)))
                if person == -1:
                    return self.selector()
                print("\033[32mOpening chat for", people[person - 1][1].text.strip(), "\033[0m")
            except (IndexError, ValueError):
                print("Please enter a valid number. [1-%d]" % len(people))
                tries -= 1
            else:
                people[person - 1][1].click()
                return True
        return False

    def do_chat(self):

        def renderer(i):
            i_soup = BeautifulSoup(i.get_attribute("innerHTML"), "html.parser")
            chunk = i_soup.get_text(separator="\n").split("\n")
            name = chunk[0]
            if len(chunk) > 1:
                msg = "\n".join(str(e) for e in chunk[1:])
            else:
                msg = None

            src = None
            if name.strip() == self.me:
                print("\033[32m" + name + ": ")
            else:
                print("\033[0m" + name + ": ")
            # Check if it's a video
            try:
                video = i_soup.find("video")
                src = "Video: " + "\n".join(str(e) for e in i_soup.get_text(separator="\n").split("\n")[0:2]) + "\n" + \
                      video["src"]
                print(msg if not src else src, "\033[0m")
                return
            except TypeError:
                pass

            # Check if it's an Image or Images
            try:
                imgs = i_soup.findAll("img")
                a_s = i_soup.findAll("a")
                if len(imgs) and len(a_s):
                    for img, a in zip(imgs, a_s):
                        src = "Image: " + "\n".join(
                            str(e) for e in img.get_text(separator="\n").split("\n")[0:2]) + "\n" + a["href"]

            except (TypeError, KeyError):
                pass

            # If not media
            if not src:
                # if text
                if msg:
                    # if text with emojis
                    if i_soup.find("span").findAll("img"):
                        text_chunks = i_soup.find("span").get_text(separator="\n").split("\n")

                        pngs = i_soup.findAll("img", attrs="_1ift")
                        for txt in text_chunks:
                            print(txt, end="")
                            if len(pngs):
                                print(pngs.pop(0)['alt'], end="")
                        print("".join(e['alt'] for e in pngs))
                    # if only text
                    else:
                        print(msg)

                # if not text but emojis
                elif i_soup.findAll("img", attrs="_1ift"):
                    for pngs in i_soup.findAll("img"):
                        print(pngs["alt"])
                else:
                    emojis = i_soup.findAll("div", attrs={"role": "img"})
                    for emoji in emojis:
                        print("Sent a", emoji["aria-label"])
            else:
                print(src)
            print("\n\033[0m")

        pre_wrapper = ''
        pre_wrapper_ele = []
        while True:
            try:
                wrapper = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "__i_"))
                )
            except SE.TimeoutException:
                print("Timed Out!")
                return
            if pre_wrapper != wrapper.text:
                iterels = wrapper.find_elements_by_xpath("//div[@class=\"_41ud\"]")
                iterels_cp = iterels[:]
                [iterels.remove(e) for e in pre_wrapper_ele if e in pre_wrapper_ele]

                if len(iterels):
                    for i in iterels:
                        renderer(i)
                else:
                    renderer(iterels_cp[-1])

                pre_wrapper = wrapper.text
                pre_wrapper_ele = iterels_cp
            typed = input_with_timeout("Press ';' to reply, 'c' to chat with others, 'x' to quit...", 3)
            print("\r", " "*60, end="\r")
            if not typed:
                print("Refreshing...", end="\r")
                print(" "*13, end="\r")
                continue
            elif typed == ";":
                reply = input("Enter your message:")
                print("\x1b[1A\x1b[2K", end="")
                if not self.driver.current_url.endswith("#"):
                    self.driver.get(self.driver.current_url+"#")
                try:
                    elem = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, "//div[contains(@class,\"_1mf _1mj\")]"))
                    )
                    elem.click()
                except Exception as e:
                    print(e)
                    pass
                action = ActionChains(self.driver)
                action.send_keys(reply+Keys.ENTER)
                action.perform()

            elif typed == 'c':
                return self.messenger()

            elif typed == 'x':
                print("Quitting Messenger! Thanks for using!")
                break


chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920, 1080")

print("Opening up Clinger...")
driver = webdriver.Chrome(executable_path="./chromedriver",
                          chrome_options=chrome_options)
obj = Clinger(driver)
driver.close()
