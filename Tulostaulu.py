# --coding:utf-8 -----
# Tulostaulu
from cmath import pi
from pickle import FALSE, TRUE
from re import X
import threading
import tkinter as tk
from tkinter import BOTTOM, ttk, filedialog
from pathlib import Path
import time
from time import ctime
from shutil import copyfile
from tkinter.constants import LEFT, RIGHT
from threading import Thread
from tkinter.messagebox import showerror
import requests
import json
import queue

INFO_TEXT_DURATION = 10

class AsyncDownload(Thread):
    def __init__(self, master, url, q):
        super().__init__()
        self.master = master
        self.queue = q
        self.update_url(url)
        self.codes = self.get_penalty_codes("Syykoodit.json")

    def run(self):
        while True:
            time.sleep(5)
            try:
                response = requests.get(self.url)
                if response.status_code == requests.codes.ok:
                    self.events = response.json()
                    self.filtered_events = self.filter_events(self.events)
                    len_filtered_events = len(self.filtered_events)
                    if self.first_request:
                        self.event_idx = len_filtered_events
                        if self.event_idx < 0:
                            self.event_idx = 0
                        self.first_request = False
                    if len_filtered_events > self.event_idx:
                        for e in self.filtered_events[self.event_idx:]:
                            self.queue.put(self.__parse_event(e)) # Output events to queue
                        self.event_idx = len_filtered_events
            except Exception as e:
                print("request exeption " + str(e))


    def update_url(self, new_url):
        self.events = []
        self.url            = new_url
        self.first_request  = True
        self.event_idx      = 0
        

    def filter_events(self, events_json):   
        e = events_json['match']['events']
        filtered = [event for event in e if event['code'] == 'maali' or event['code'] == '2min']
        return filtered

    def __parse_event(self, event):
        if event['code'] == 'maali':     # Maalit valitaan aina
            return self.__parse_scorer(event)
        elif event['code'] == '2min':
            return self.__parse_penalty(event)
        # elif event['type'] == 'timeoutEvent':
        #     return self.parse_timeout(event)
        else:
            return '???'

    def __parse_scorer(self, goal):
        score     = str(goal['description'])
        if goal['team'] == 'A':
            scoring_team = self.events['match']['team_A_name']
        elif goal['team'] == 'B':
            scoring_team = self.events['match']['team_B_name']
        else:
            scoring_team        = str("")

        scorer_number       = "#" + str(goal['shirt_number'])
        scorer_Name    = str(goal['player_name'])

        scorer_text = " ".join(["Maali", scoring_team, scorer_number, scorer_Name, score])
        return scorer_text

    def get_penalty_codes(self, file_name="Syykoodit.json"):
        with open(file_name, encoding='utf-8') as json_file:
            codes = json.load(json_file)
        return codes

    
    def __parse_penalty(self, penalty):
        if penalty['team'] == 'A':
            penalty_drawing_team = self.events['match']['team_A_name']
        elif penalty['team'] == 'B':
            penalty_drawing_team = self.events['match']['team_B_name']
        else:
            penalty_drawing_team        = str("")
        penalty_drawing_number       = "#" + str(penalty['shirt_number'])
        penalty_drawing_player = penalty['player_name']

        fault_name = str(self.codes[penalty['description']])
        penalty_text = " ".join(["Jäähy", penalty_drawing_team, penalty_drawing_number, penalty_drawing_player, fault_name])
        return penalty_text

    def parse_timeout(self, timeout):
        timeout_taking_team = str(timeout['team']['name'])
        timeout_text = " ".join(["Aikalisä", timeout_taking_team])
        return timeout_text


class InfoWriter(Thread):
    def __init__(self, master, q, i_face):
        super().__init__()
        self.master = master
        self.queue = q
        self.interface_folder = i_face
        self.should_clear_queue = False

    def run(self):
        while True:
            try:
                info_text = self.queue.get()
            except queue.Empty:
                pass
            else:
                self.master.lbl_scorer.configure(text=info_text)
                self.write_info()
                time.sleep(INFO_TEXT_DURATION)
                self.clear_info()

            if self.should_clear_queue:
                with self.queue.mutex:
                    self.queue.queue.clear()
                    print("Pino tyhjennetty")
                    self.should_clear_queue = False

    def write_info(self):
        with open('Infoteksti.txt', encoding='utf-8', mode='w') as file:
            file.write(str(self.master.lbl_scorer.cget("text")))

    def clear_info(self):
        with open('Infoteksti.txt', encoding='utf-8', mode='w') as file:
            file.write("")


class NumeroNaytto(tk.Frame):
    def __init__(self, master, otsikko, *args, **kwargs):
        tk.Frame.__init__(self, master, *args, **kwargs)
        self.numero = tk.StringVar()
        self.internalNumber = 0
        self.tiedostonNimi = otsikko + '.txt'
        self.numero.set(str(self.internalNumber))
        
        self.btn_plus = tk.Button(self, width=4, height=2, text= u"\u25b2", command=self.numero_plus)
        self.btn_miinus = tk.Button(self, width=4, height=2, text= u"\u25bc", command=self.numero_miinus)
        # self.lbl_otsikko = tk.Label(self, text=otsikko)
        self.lbl_numero = tk.Label(self, font=('Lucida Sans Unicode MS', 24), textvariable=self.numero, width=2, relief='sunken')

        # self.pack_propagate(False)

        # self.lbl_otsikko.pack()
        self.btn_plus.pack()
        self.lbl_numero.pack()    
        self.btn_miinus.pack()

        # Luo tiedosta ja alusta
        with open(otsikko + '.txt','w')  as f:
            f.write("0")
        
    def numero_plus(self):
        self.internalNumber += 1
        self.numero.set(str(self.internalNumber))
        with open(self.tiedostonNimi,'w')  as f:
            f.write(str(self.internalNumber))

    def numero_miinus(self):
        self.internalNumber -= 1
        if self.internalNumber < 0:
            self.internalNumber = 0
        self.numero.set(str(self.internalNumber))
        with open(self.tiedostonNimi,'w')  as f:
            f.write(str(self.internalNumber))


class JoukkueNaytto(tk.Frame):
    def __init__(self, master, joukkueet, otsikko, *args, **kwargs):
        tk.Frame.__init__(self, master, *args, **kwargs)
        self.joukkueet = joukkueet
        self.tiedostonNimi = otsikko + '.txt'
        self.joukkeValinta = tk.StringVar()
        
        # Lue joukkueet tiedostosta
        joukkueet = []
        with open(self.joukkueet, encoding='utf-8') as inFile:
            joukkueet = [line.strip('\n') for line in inFile]

        # with open(self.tiedostonNimi, encoding='utf-8', mode='w')  as self.tiedosto:
        #     print(self.tiedostonNimi)
        #     pass

        self.cb_joukkueValinta = ttk.Combobox(self, textvariable=self.joukkeValinta, state='readonly')
        self.cb_joukkueValinta['values'] = sorted(joukkueet)
        self.cb_joukkueValinta.bind("<<ComboboxSelected>>", self.joukkueValittu)
        
        self.cb_joukkueValinta.pack()

    def joukkueValittu(self, event):
        print(self.joukkeValinta.get())
        with open(self.tiedostonNimi,'w', encoding='utf-8')  as f:
            f.write(self.joukkeValinta.get())


class EraNaytto(tk.Frame):
    def __init__(self, master, otsikko, *args, **kwargs):
        tk.Frame.__init__(self, master, *args, **kwargs)

        self.eraValinta = tk.StringVar(master, "1")

        # Luo tiedosta ja alusta
        self.tiedostonNimi = otsikko + '.txt'
        with open(self.tiedostonNimi, encoding='utf-8', mode='w')  as f:
            f.write(self.eraValinta.get())


        eraTekstit = [
            ('1.Erä',   '1'),
            ('2.Erä',   '2'),
            ('3.Erä',   '3'),
            ('JA',      'JA'),
            ('Tauko',   'Tauko'),
        ]

        for teksti, eraTeksti in eraTekstit:
            tk.Radiobutton(self, 
                        text=teksti,
                        indicatoron = 0,
                        padx = 20, 
                        variable=self.eraValinta, 
                        command=self.NaytaValinta,
                        value=eraTeksti).pack(anchor=tk.W)

    def NaytaValinta(self):
        with open(self.tiedostonNimi, encoding='utf-8', mode='w')  as f:
            f.write(self.eraValinta.get())  


class Ohjaus(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        tk.Frame.__init__(self, master, *args, **kwargs)

        self.replayTiedosto = Path(filedialog.askopenfilename())
        print(self.replayTiedosto)
        self.tallennusPolku = Path(filedialog.askdirectory())
        print(self.tallennusPolku)

        self.btn_tallenna = tk.Button(self, text='Tallenna', command=self.tallennaTiedosto)
        self.lbl_aika = tk.Label(self, text="")

        # self.btn_tallenna.pack()
        self.lbl_aika.pack()

        self.update_clock()

    def tallennaTiedosto(self):
        uusintaTiedosto = time.strftime("%H%M%S_" + 
        self.frm_era.eraValinta.get().replace('.', '').replace('ä', 'a') + '_' +
        self.frm_koti.numero.get() + '-' +
        self.frm_vieras.numero.get() +
        '.mkv'
        )
        print(uusintaTiedosto)
        copyfile(self.replayTiedosto, self.tallennusPolku / uusintaTiedosto)
        
    def update_clock(self):
        now = time.strftime("%H:%M:%S")
        self.lbl_aika.configure(text=now)
        self.after(1000, self.update_clock)


class LiveNaytto(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        tk.Frame.__init__(self, master, *args, **kwargs)
        self.master = master
        self.get_settings('Asetukset.json')
        self.info_queue = queue.Queue(10)

        self.writer_thread = InfoWriter(self, self.info_queue, self.rajapinta_hakemisto)
        self.writer_thread.daemon = TRUE

        self.event_thread = AsyncDownload(self, self.endpoint, self.info_queue)
        self.event_thread.daemon = TRUE

        self.frm_label              = tk.LabelFrame(self)
        self.frm_buttons            = tk.Frame(self)
        self.lbl_scorer             = tk.Label(self.frm_label , text="", anchor=tk.W)
        self.btn_set_info           = tk.Button(self.frm_buttons, text="Kirjoita", command=lambda: self.writer_thread.write_info())
        self.btn_clear_info         = tk.Button(self.frm_buttons, text="Tyhjennä", command=lambda: self.writer_thread.clear_info())
        self.btn_update_settings    = tk.Button(self.frm_buttons, text="Päivitä", command=lambda: self.update_game_id())

        self.lbl_scorer.pack(fill=tk.X)

        self.btn_set_info.pack(side='left')
        self.btn_clear_info.pack(side='left')
        self.btn_update_settings.pack()

        self.frm_label.pack(fill=tk.X)
        self.frm_buttons.pack(side='left')

        self.writer_thread.start()
        self.event_thread.start()    

    def get_settings(self, file_name):
        with open(file_name) as json_file:
            setup = json.load(json_file)

        # Endpoint
        protocoll =     setup['protocoll']
        domain =        setup['domain']
        path =          setup['path']

        # Query Parameters
        api_key =   setup['api_key']
        match_id =  setup['match_id']

        self.endpoint = protocoll + domain + path + "&api_key=" + api_key + "&match_id=" + match_id
        self.rajapinta_hakemisto = setup['Obs_interface_path'] + "\\"
        return setup
        

    def update_game_id(self):
        config = self.get_settings('Asetukset.json')
        self.event_thread.update_url(self.endpoint)
        self.master.update_master_title(config['api_key'], config['match_id'])
        self.writer_thread.should_clear_queue = True


class MyApp(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        tk.Frame.__init__(self, master, *args, **kwargs)
        self.master = master

        # Read interface folder location
        with open('Asetukset.json', 'r') as f_config:
            config_dict = json.load(f_config)    
            rajapinta_hakemisto = config_dict['Obs_interface_path'] + "\\" 
            ottelu_id = config_dict['match_id']
            api_key = config_dict['api_key']
        
        # Set master title
        self.update_master_title(api_key, ottelu_id)

        frm_koti = NumeroNaytto(self, rajapinta_hakemisto + "Koti", width=50, height=130,bd=2, relief='groove')
        frm_koti.pack_propagate(False)

        frm_era = EraNaytto(self, rajapinta_hakemisto + "Era", width=60, height=130,bd=2, relief='groove')
        frm_era.pack_propagate(False)

        frm_vieras = NumeroNaytto(self, rajapinta_hakemisto + "Vieras", width=50, height=130,bd=2, relief='groove')
        frm_vieras.pack_propagate(False)

        frm_kotijoukkue = JoukkueNaytto(self, "Joukkueet.txt", rajapinta_hakemisto + "Kotijoukkue", width=80, height=130,bd=2, relief='groove')
        frm_kotijoukkue.pack_propagate(False)

        frm_vierasjoukkue = JoukkueNaytto(self, "Joukkueet.txt", rajapinta_hakemisto + "Vierasjoukkue", width=80, height=130,bd=2, relief='groove')
        frm_vierasjoukkue.pack_propagate(False)

        frm_ohjaus = Ohjaus(self, width=120, height=130, bd=2, relief='groove')
        frm_live = LiveNaytto(self, height=130, bd=2, relief='groove')

        frm_ohjaus.grid(row=0, column=0)
        frm_kotijoukkue.grid(row=0, column=1)
        frm_koti.grid(row=0, column=2)
        frm_era.grid(row=0, column=3)
        frm_vieras.grid(row=0, column=4)
        frm_vierasjoukkue.grid(row=0, column=5)
        frm_live.grid(row=1, sticky='ew', column=0, columnspan=6)

    def update_master_title(self, api_key, match_id):
        url = r"https://salibandy.api.torneopal.com/taso/rest/getMatch&api_key=" + api_key + "&match_id=" + match_id
        response = requests.get(url, timeout=10)

        if response.status_code == requests.codes.ok:
            game_data = response.json()
            try:
                home_team = game_data['match']['team_A_name']
                away_team = game_data['match']['team_B_name']
                title = home_team + " vs " + away_team
            except Exception as e:
                title = "???"
        else:
            title = "???"
        self.master.title(title) 

# def tallenna(event=None):
#     print("Easy!")

# hk = SystemHotkey()
# hk.register(('6',), callback=lambda event: tallenna())


if __name__ == "__main__":
    root = tk.Tk()
    root.title('Jee')
    MyApp(root).pack(side="top", fill="both", expand=True)
    root.mainloop()
