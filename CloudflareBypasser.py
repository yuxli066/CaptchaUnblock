import time
from DrissionPage import ChromiumPage
import subprocess
import json

class CloudflareBypasser:
    def __init__(self, driver: ChromiumPage, max_retries=-1, log=True):
        self.driver = driver
        self.max_retries = max_retries
        self.log = log

    def search_recursively_shadow_root_with_iframe(self,ele):
        if ele.shadow_root:
            if ele.shadow_root.child().tag == "iframe":
                return ele.shadow_root.child()
        else:
            for child in ele.children():
                result = self.search_recursively_shadow_root_with_iframe(child)
                if result:
                    return result
        return None

    def search_recursively_shadow_root_with_cf_input(self,ele):
        if ele.shadow_root:
            if ele.shadow_root.ele("tag:input"):
                return ele.shadow_root.ele("tag:input")
        else:
            for child in ele.children():
                result = self.search_recursively_shadow_root_with_cf_input(child)
                if result:
                    return result
        return None
    
    def locate_cf_button(self):
        button = None
        eles = self.driver.eles("tag:input")
        for ele in eles:
            if "name" in ele.attrs.keys() and "type" in ele.attrs.keys():
                if "turnstile" in ele.attrs["name"] and ele.attrs["type"] == "hidden":
                    button = ele.parent().shadow_root.child()("tag:body").shadow_root("tag:input")
                    break
            
        if button:
            return button
        else:
            return None
            # there's actually no need to search recursively for Indeed.
            # If the button is not found, search it recursively
            # self.log_message("Basic search failed. Searching for button recursively.")
            # ele = self.driver.ele("tag:body")
            # iframe = self.search_recursively_shadow_root_with_iframe(ele)
            # if iframe:
            #     button = self.search_recursively_shadow_root_with_cf_input(iframe("tag:body"))
            # else:
            #     self.log_message("Iframe not found. Button search failed.")
            # return button

    def log_message(self, message):
        if self.log:
            print(message)

    def click_verification_button(self):
        try:
            button = self.locate_cf_button()
            if button:
                self.log_message("Verification button found. Attempting to click.")
                button.click()
            else:
                self.log_message("Verification button not found.")
                raise Exception('Button not found!')

        except Exception as e:
            self.log_message(f"Error clicking verification button: {e}")

    def is_bypassed(self):
        try:
            title = self.driver.title.lower()
            return "just a moment" not in title
        except Exception as e:
            self.log_message(f"Error checking page title: {e}")
            return False

    def tryBypass(self):
        try_count = 0
        while not self.is_bypassed():
            if 0 < self.max_retries + 1 <= try_count:
                self.log_message("Exceeded maximum retries. Bypass failed.")
                break
            self.log_message(f"Attempt {try_count + 1}: Verification page detected. Trying to bypass...")
            self.click_verification_button()
            try_count += 1
            time.sleep(2)
        
        if self.is_bypassed():
            self.log_message("Bypass successful!!!")
            time.sleep(2)

    def clickIfVisible(self, cssSel:str, selName:str): 
        try:
            self.driver.wait.ele_displayed("css:{}".format(cssSel), timeout=2)
            self.driver.wait.eles_loaded("css:{}".format(cssSel), timeout=2)
            sel = self.driver.ele("css:{}".format(cssSel), timeout=2)
            sel.click()
        except Exception as e:
            print("{} btn could not be found again, it's okay, moving on...".format(selName))

    def bypass(self, login: bool):
        
        # indeed login steps, MODULARIZE ME.
        node_script = "/Users/leoli/WebstormProjects/job-hunt/services/google/getEmails.ts"

        if login: 
                try:
                    self.tryBypass()
                    print('Logging in.')
                    
                    emailInput = self.driver.ele('css:[id="ifl-InputFormField-:r0:"]')
                    emailInput.input("leoli7405@gmail.com")
                    
                    self.clickIfVisible('[data-tn-element="auth-page-email-submit-button"]', 'Continue')
                    self.tryBypass()
                    self.clickIfVisible('[data-tn-element="auth-page-email-submit-button"]', 'Continue')

                    self.driver.wait.ele_displayed("css:{}".format('[data-tn-element="auth-page-google-password-fallback"]'), timeout=2)
                    signInWithCodeInstead = self.driver.ele('css:[data-tn-element="auth-page-google-password-fallback"]')
                    signInWithCodeInstead.click()

                    time.sleep(10)
                    print("Waiting 10s for new code...")

                    # Execute the Node.js script
                    try:
                        cmd = ["tsx", node_script]
                        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
                        out = res.stdout.strip()
                        err = res.stderr.strip()
                        codes = out.replace('OTP code: ','')
                        codesJson = json.loads(codes)
                    except subprocess.CalledProcessError as e:
                        print("Email Script STDOUT ->", e.stdout)
                        print("Email Script STDERR ->", e.stderr)
                        print("Email Script STDERR (original) ->", err)
                        raise
                    
                    if codesJson:
                        print("TOKEN", codesJson[0])
                        tokenInput = self.driver.ele('css:[aria-describedby="label-passcode-input-error"]')
                        time.sleep(10)
                        tokenInput.input(codesJson[0])
                        
                        self.clickIfVisible('[data-tn-element="otp-verify-login-submit-button"]', 'Signin')
                        self.tryBypass()
                        self.clickIfVisible('[data-tn-element="otp-verify-login-submit-button"]', 'Signin')
                        self.clickIfVisible('[id="pass-WebAuthn-continue-button"]', 'Not Now')

                        self.driver.get('https://www.indeed.com', retry=3, timeout=30)
                        self.driver.wait.ele_displayed('css:[id="AccountMenu"]', timeout=30, raise_err=True)
                        accountMenu = self.driver.ele('css:[id="AccountMenu"]')
                        accountMenu.focus()
                        accountMenu.hover()
                        accountMenu.click()
                    else: 
                        self.log_message("Email Script Failed.")
                
                except Exception as e:
                    print(e)
                    raise e
        else:
            self.tryBypass()
            if self.is_bypassed():
                self.log_message("Bypass successful.")
            else:
                self.log_message("Bypass failed.")
