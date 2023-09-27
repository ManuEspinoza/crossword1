import pandas as pd

word_list = list()
with open('words.txt') as wordlist_file:
     for i, word in enumerate(wordlist_file.readlines()):
         word_list.append([word.strip().lower(), '', i, i, i])

words_dataframe = pd.DataFrame(data=word_list,
                                columns=['word_label_text',
                                         'word_description_text',
                                         'word_concept_id',
                                         'word_label_id',
                                         'word_description_id'])

words_dataframe.to_pickle('wordlist.pickle.gzip', compression='gzip', protocol=5)