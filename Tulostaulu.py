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
        self.events = []
        self.url = url
        self.first_request = True
        self.event_idx = 0

    def run(self):
        while True:
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
                            self.queue.put(self.parse_event(e)) # Output events to queue
                        self.event_idx = len_filtered_events
            except Exception as e:
                print(e)
            time.sleep(5)

    def filter_events(self, events_json):
        output_events_json = [x for x in events_json if 
        x['type'] == 'goal' or 
        x['type'] == 'penalty' or 
        x['type'] == 'timeoutEvent']
        return output_events_json

    def parse_event(self, event):
        if event['type'] == 'goal':
            return self.parse_scorer(event)
        elif event['type'] == 'penalty':
            return self.parse_penalty(event)
        elif event['type'] == 'timeoutEvent':
            return self.parse_timeout(event)
        else:
            return '???'

    def parse_scorer(self, goal):
        home_team_score     = str(goal['homeTeamScore'])
        away_team_score     = str(goal['awayTeamScore'])
        scoring_team        = str(goal['scoringTeam']['name'])
        if goal['ownGoal']: # jos oma maali
            scorer_number       = ""
            scorer_firstName    = "Oma"
            scorer_lastName     = "maali"
        else:
            scorer_number       = "#" + str(goal['scorerLineup']['number'])
            scorer_firstName    = str(goal['scorer']['firstName'])
            scorer_lastName     = str(goal['scorer']['lastName'])

        scorer_text = " ".join([scoring_team, home_team_score, "-", away_team_score, scorer_number, scorer_firstName, scorer_lastName])
        return scorer_text

    def parse_penalty(self, penalty):
        penalty_drawing_team = str(penalty['team']['name'])
        fault_name = str(penalty['faultName'])
        penalty_text = " ".join(["Jäähy", penalty_drawing_team, fault_name])
        return penalty_text

    def parse_timeout(self, timeout):
        timeout_taking_team = str(timeout['team']['name'])
        timeout_text = " ".join(["Aikalisä", timeout_taking_team])
        return timeout_text

class InfoWriter(Thread):
    def __init__(self, master, q):
        super().__init__()
        self.master = master
        self.queue = q

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

        self.get_settings('Asetukset.json')
        self.info_queue = queue.Queue(10)

        self.writer_thread = InfoWriter(self, self.info_queue)
        self.writer_thread.daemon = TRUE

        self.event_thread = AsyncDownload(self, self.endpoint, self.info_queue)
        self.event_thread.daemon = TRUE

        self.frm_label              = tk.LabelFrame(self)
        self.frm_buttons            = tk.Frame(self)
        self.lbl_scorer             = tk.Label(self.frm_label , text="", anchor=tk.W)
        self.btn_set_info           = tk.Button(self.frm_buttons, text="Kirjoita", command=self.writer_thread.write_info)
        self.btn_clear_info         = tk.Button(self.frm_buttons, text="Tyhjennä", command=self.writer_thread.clear_info)
        self.btn_update_settings    = tk.Button(self.frm_buttons, text="Asetukset", command=lambda: self.get_settings('Asetukset.json'))

        # self.frm_label.grid(row=0, column=0, sticky='ew')
        # self.frm_buttons.grid(row=1, column=0)
        # self.lbl_scorer.grid(row=0, column=0, sticky='ew')
        # self.btn_set_info.grid(row=1, column=0, sticky='w')
        # self.btn_clear_info.grid(row=1, column=1, sticky='w')
        # self.btn_update_settings.grid(row=1, column=2, sticky='w')

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

            url         = setup['Url']
            apiPath     = setup['Apipath']
            ottelu_ID   = setup['GameId']
        
        self.endpoint = url + '/' + apiPath + '/' + ottelu_ID
        self.payload = {'grouped': '1'}


class MyApp(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        tk.Frame.__init__(self, master, *args, **kwargs)
        self.master = master

        frm_koti = NumeroNaytto(self, "Koti", width=50, height=130,bd=2, relief='groove')
        frm_koti.pack_propagate(False)

        frm_era = EraNaytto(self, "Era", width=60, height=130,bd=2, relief='groove')
        frm_era.pack_propagate(False)

        frm_vieras = NumeroNaytto(self, "Vieras", width=50, height=130,bd=2, relief='groove')
        frm_vieras.pack_propagate(False)

        frm_kotijoukkue = JoukkueNaytto(self, "Joukkueet.txt", "Kotijoukkue", width=80, height=130,bd=2, relief='groove')
        frm_kotijoukkue.pack_propagate(False)

        frm_vierasjoukkue = JoukkueNaytto(self, "Joukkueet.txt", "Vierasjoukkue", width=80, height=130,bd=2, relief='groove')
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

# def tallenna(event=None):
#     print("Easy!")

# hk = SystemHotkey()
# hk.register(('6',), callback=lambda event: tallenna())


if __name__ == "__main__":
    root = tk.Tk()
    MyApp(root).pack(side="top", fill="both", expand=True)
    root.mainloop()