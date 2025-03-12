import time
import pandas as pd
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

class SintaScraper:
    def __init__(self):
        self.driver = None
        self.url = "https://sinta.kemdikbud.go.id/affiliations/profile/398/?page={}&view=googlescholar"
        self.records = {key: [] for key in ["Judul", "Tahun", "Penulis", "Publikasi", "Dikutip", "Link"]}
        # self.data = {
        #     "Judul": [],
        #     "Tahun": [],
        #     "Penulis": [],
        #     "Publikasi": [],
        #     "Dikutip": [],
        #     "Link": []
        # }
    
    def initialize_browser(self):
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--log-level=3")  
        
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_page_load_timeout(120)  
    
    def login(self, username, password):
        self.driver.get("https://sinta.kemdikbud.go.id/logins")
        try:
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.NAME, "username"))
            ).send_keys(username)
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.NAME, "password"))
            ).send_keys(password)
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Login')]")
            )).click()
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "navbar-brand"))
            )
            print("Login berhasil!")
        except Exception as e:
            print(f"Gagal login: {e}")
            self.driver.quit()
    
    def extract_publications(self, start_page=1, end_page=834):
        for page in range(start_page, end_page + 1):
            retry_attempts = 3  # Maksimal 3 kali mencoba ulang jika error
            while retry_attempts > 0:
                try:
                    print(f"Scraping page {page}")
                    self.driver.get(self.url.format(page))
                    time.sleep(5)
                    soup = BeautifulSoup(self.driver.page_source, "lxml")
                    articles = soup.find_all("div", class_="ar-list-item")
                    
                    if not articles:
                        print(f"Tidak ada artikel di halaman {page}.")
                        break
                    
                    for article in articles:
                        try:
                            artikel_data = {
                                "Judul": article.find("div", class_="ar-title").find("a").text.strip(),
                                "Tahun": article.find("a", class_="ar-year").text.strip(),
                                "Penulis": article.select_one(".ar-meta a[href]").text.strip(),
                                "Publikasi": article.find("a", class_="ar-pub").text.strip(),
                                "Dikutip": article.find("a", class_="ar-cited").text.strip() if article.find("a", class_="ar-cited") else "0",
                                "Link": article.find("div", class_="ar-title").find("a")["href"]
                            }
                            for key, value in artikel_data.items():
                                self.records[key].append(value)
                        except Exception as e:
                            print(f"Kesalahan saat mengambil data artikel: {e}")
                            continue
                    
                    break 

                except TimeoutException:
                    print(f"Timeout saat mengambil halaman {page}, mencoba ulang...")
                    retry_attempts -= 1
                except WebDriverException as e:
                    print(f"Kesalahan WebDriver pada halaman {page}: {e}")
                    retry_attempts -= 1
                except Exception as e:
                    print(f"Kesalahan tidak terduga pada halaman {page}: {e}")
                    retry_attempts -= 1

            if retry_attempts == 0:
                print(f"Gagal mengambil data dari halaman {page} setelah beberapa kali percobaan.")


    def export_to_csv(self, filename="Hasil Scraping Google Scholar Sinta Universitas Lampung.csv"):
        pd.DataFrame(self.records).to_csv(filename, index=False)
        print(f"Data disimpan dalam {filename}")
    
    def execute(self, username, password):
        self.initialize_browser()
        self.login(username, password)
        self.extract_publications()
        self.export_to_csv()
        self.driver.quit()
        print("Scraping selesai!")

if __name__ == "__main__":
    scraper = SintaScraper()
    scraper.execute("igit.sabda@fmipa.unila.ac.id", "1G1t01011996")
