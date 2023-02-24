import sys
import time
import requests
import xmltodict, json
import PyPDF2
from io import BytesIO, SEEK_SET, SEEK_END 

class ResponseStream(object):
      
    def __init__(self, request_iterator):
        self._bytes = BytesIO()
        self._iterator = request_iterator
   
    def _load_all(self):
        self._bytes.seek(0, SEEK_END)
          
        for chunk in self._iterator:
            self._bytes.write(chunk)
   
    def _load_until(self, goal_position):
        current_position = self._bytes.seek(0, SEEK_END)
          
        while current_position < goal_position:
            try:
                current_position = self._bytes.write(next(self._iterator))
                  
            except StopIteration:
                break
   
    def tell(self):
        return self._bytes.tell()
   
    def read(self, size = None):
        left_off_at = self._bytes.tell()
          
        if size is None:
            self._load_all()
        else:
            goal_position = left_off_at + size
            self._load_until(goal_position)
   
        self._bytes.seek(left_off_at)
          
        return self._bytes.read(size)
   
    def seek(self, position, whence = SEEK_SET):
          
        if whence == SEEK_END:
            self._load_all()
        else:
            self._bytes.seek(position, whence)


isbn = input("Inserisci l'isbn del tuo libro: ")
cookie = input("Inserisci i cookie: ")
merger = PyPDF2.PdfFileWriter()
#estrapolo volume.xml del libro
volumexml = requests.get('https://web-booktab.zanichelli.it/api/v1/resources_web/' + isbn + '/volume.xml', headers = {'Cookie':cookie})
if (volumexml.status_code == 302):
  print('Cookie errati, prova di nuovo!')
  sys.exit()
elif (volumexml.status_code != 200):
  print('ISBN errato o sito non più raggiungibile, prova di nuovo!')
  sys.exit()
else:
  json = xmltodict.parse(volumexml.text)
  title = json['config']['volume']['settings']['volumetitle'] #titolo del libro
  titolo = title + ".pdf" #titolo da salvare in pdf
  array_unita = json['config']['volume']['units']['unit']
  print("\nLibro: " + title + "\n")
  time.sleep(2)
  print("Download dei capitoli in corso...")
  for unittitle in array_unita:
    if '@plusbook' not in unittitle or unittitle['@plusbook'] == '10': #plusbook deve essere nullo o avere valore 10, diverso comunque da -1
      id_unit = unittitle['@btbid']
      config_xml = requests.get('https://web-booktab.zanichelli.it/api/v1/resources_web/' + isbn + '/' + id_unit + '/config.xml', headers = {'Cookie':cookie})
      config_json = xmltodict.parse(config_xml.text)
      if 'content' in config_json['unit']:
        content2 = config_json['unit']['content'] + ".pdf"
        entry = config_json['unit']['filesMap']['entry']
        for entry in entry:
            if entry['@key'] == content2:
              richiesta = requests.get('https://web-booktab.zanichelli.it/api/v1/resources_web/' + isbn + '/' + id_unit + '/' + entry['#text'] + ".pdf", headers = {'Cookie':cookie})
              pdf = PyPDF2.PdfFileReader(ResponseStream(richiesta.iter_content(64)))
              print('Download completato di: ' + content2)
              for page in range(pdf.getNumPages()):
                 merger.addPage(pdf.getPage(page))
  with open(titolo, 'wb') as g:
    print('Merging dei capitoli in corso...')
    merger.write(g)
print("Concluso! Trovi il pdf nella cartella dello script")
exit()