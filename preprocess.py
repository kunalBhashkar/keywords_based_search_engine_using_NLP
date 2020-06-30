# importing packages
import math
import pandas as pd
import numpy as np
import re
import nltk
from nltk.corpus import stopwords

from nltk.corpus import stopwords
nltk.download('stopwords')
from nltk.tokenize import word_tokenize
import logging
from flask import Flask,Blueprint, flash, redirect, render_template, request, url_for,json,current_app, jsonify


#Method
def preprocess():
    try:
        test_json=" "
        test_json = request.get_json()
    except Exception as e:
        pass

    if test_json==None:        
        Observation=request.form.get('message')  
    else:
        Observation=test_json["message"]
    try:
        df1=pd.read_excel("./SIRE_dataset/REFERENCE_Checklist_VIQ_Chapter_4_Revision_9_new_approach.xlsx",sheet_name=0,skiprows=[0,1])
        # initialize list of lists 
        data = [[4.1,4.12,Observation]] 
        # Create the pandas DataFrame 
        df2 = pd.DataFrame(data, columns = ['Viq Ref', 'Unnamed: 1','Inspector Observation'])
        
        #rename columns
        df1.rename(columns={"VIQ 7 Q.No":"VIQ_No","Sub \nQ No.":"Sub_VIQ_NO","ITEM TO CHECK ":"item_check_Keywords_old","Red Marked":"essential_Keywords","Primary ":"item_check_Keywords","Secondary":"nature_check_Keywords","Support":"new_nature_check_keywords"},inplace=True)       
        pass
    except OSError as e:
        print(e.errno)
        pass
    #Method to fill null value into empty list   
    def isnan(x):
        if isinstance(x, (int,float, complex)) and math.isnan(x):
            return True
    #Assign null value into empty list
    df1=df1.apply(lambda x:x.apply(lambda x:[] if isnan(x) else x))

    #Method to stemmed string
    def stemmed_string(str1):
        '''Method to stemmed string'''
        # importing modules
        from nltk.tokenize import word_tokenize
        from nltk.stem import WordNetLemmatizer
        lemmatizer = WordNetLemmatizer() 
        # initialize an empty string 
        str1=str(str1)
        str1=str1.replace("'","")
        str2 = "" 
        str1=" ".join(str1.split())
        words = word_tokenize(str1)
        for w in words: 
            stem_word=lemmatizer.lemmatize(str(w))
            str2 += " "+stem_word
            str2=str2.strip()
        return str2
    
    #Method for preprocessing steps
    def VIQ_reference_preprocessing(row):
            '''Method to pre-processing Item to Check column from reference checklist data'''
            l1=[]        
            regex1 = re.compile("[@_!#$%^*<>?/\|}{~:]")   
            row=str(row)
            # Pass the string in search  
            # method of regex object.     
            if(regex1.search(row) != None): 
                temp=((row.split('[')[0]).strip('\n'))
                l1=list(row.split('[', 1)[1].split(']'))    
                temp=stemmed_string(temp)
                l1.append(temp)
            else:    
                row=stemmed_string(row)            
                l1.append(row)            
            l2=[]
            l3=[]
            for i in l1:
                regex = re.compile('[^a-zA-Z0-9]')
                #First parameter is the replacement, second parameter is your input string
                word=regex.sub(' ',str(i))
                word=word.lstrip()                
                #print(word)#l1=list(''.join(word))
                #words=re.sub(r"^\s+", "", word), sep='') 
                l2.append((word))
                while("" in l2) : 
                    l2.remove("")
                l2 = [x.strip(' ') for x in l2]
                my_list=", ".join(l2)
                mylist = my_list.replace('  ',',')
                pattern = re.compile("^\s+|\s*,\s*|\s+$")
                l3=[x for x in pattern.split(mylist) if x]
                l4=[]
                for word_list in l3:
                        word_list=word_list.lower()  
                        word_list=stemmed_string(word_list)                      
                        l4.append(word_list)
            return sorted(list(l4),key=len,reverse=True)
    #Applying preprocessing method to item to check 
    df3=df1
    df3["essential_Keywords"]=df1["essential_Keywords"].apply(VIQ_reference_preprocessing)
    df3["item_check_Keywords"]=df1["item_check_Keywords"].apply(VIQ_reference_preprocessing)
    #Applying methods for removing bad characters from Nature of check column in reference checklist sheet
    df3["nature_check_Keywords"]=df1["nature_check_Keywords"].apply(VIQ_reference_preprocessing) 
    #rename columns
    df2.rename(columns={"Viq Ref":"VIQ_No","Unnamed: 1":"Sub_VIQ_NO","Inspector Observation":"Observation"},inplace=True)

    #Methods to remove bad characters
    def rm_bad_characters(text):
        '''method to remove bad characters'''  
        list_temp2=list()
        regex = re.compile('[^a-zA-Z0-9]')
        result=regex.sub(' ',str(text))
        text1 = re.sub('[^a-zA-Z0-9]', ' ',str(result))
        text3=re.sub("&lt;/?.*?&gt;"," &lt;&gt; ",text1) #tags remove
        text4=re.sub("(\\d|\\W)+"," ",text3)  # remove special characters and digits
        text_tokens = word_tokenize(text4)
        tokens_without_sw = [word for word in text_tokens if not word in stopwords.words()]
        text4 = (" ").join(tokens_without_sw)        
        result2=text4.lstrip()
        result2 = result2.lower()
        result2=result2.replace('was', '')
        result2=result2.replace('has', '')
        result2=stemmed_string(result2) 
        bad_chars = [';', ':', '!', "*","?","=","-"]        
        for i in bad_chars :
            test_string = ''.join(i for i in result2 if not i in bad_chars) 
            result3 = re.sub(r'[.*?[@_!#$%^*=<>?/\|}{~:]', '', test_string) 
            #result4 = ' '.join(s for s in result3.split() if not any(c.isdigit() for c in s))
            result4=re.sub("\S*\d\S*", "", result3).strip()
        list_temp1=result4.split()    
        for word in list_temp1:
            if len(word)>1:
                list_temp2.append(word)
            else:
                continue
        result5=' '.join(s for s in list_temp2)
        return result5 
    
    #Applying methods for removing bad characters from Nature of check column in reference checklist sheet
    df4=df2
    df4["Observation"]=df2["Observation"].apply(rm_bad_characters)         

    #Methods to parse the observation
    def parsed_observation(input_text):
        '''Method to parse Observation from Observation sheet or Nature of check from reference checklist sheet'''
        from rake_nltk import Rake
        import re
        import string
        # Uses stopwords for english from NLTK, and all puntuation characters by
        # default
        r = Rake()
        text=str(input_text)
        #pattern = re.compile(r'\b(' + r'|'.join(stopwords.words('english')) + r')\b\s*')
        #text = pattern.sub('', text)
        #input_str = text.lower()    
        result1 = re.sub(r'\d+','', text)    
        result2 = result1.translate(str.maketrans("","",string.punctuation))
        r.extract_keywords_from_text(result2)
        # Extraction given the list of strings where each string is a sentence.
        #r.extract_keywords_from_sentences(<list of sentences>)
        # To get keyword phrases ranked highest to lowest.
        r.get_ranked_phrases()
        # To get keyword phrases ranked highest to lowest with scores.
        keywords_ranked_phrases=r.get_ranked_phrases_with_scores()
        my_list=[]
        my_list_final=[]
        for (i,j) in keywords_ranked_phrases:       
            my_list.append(j)
        pattern = "[0-9,).(!?]*"
        my_list_new = [re.sub(pattern, '', i) for i in my_list]
        while("" in my_list_new) : 
            my_list_new.remove("")
        for word in my_list_new:
            if len(word)>1:
                my_list_final.append(word)
            else:
                continue
        return sorted(list(set(my_list_final)),key=len,reverse=True)

    #Creating a new field and assigning parsed value of Nature of check from reference checklist sheet
    df4["parsed_keywords"]=df4["Observation"].apply(parsed_observation)   

    #getting combined list of Item to check
    item_check_remove_list=["two way","and","&","test","safe"]
    dict_replace_item_check={"off course alarm":"course alarm","sat c":"sat","company sm":"company","ex rated mobile phone":"mobile phone","electronic chart display and information system":"electronic chart display information system","position fixing method":"position fixing"}
    
    #getting combined list of Essential keyword
    combined_list_essential_Keywords=list()
    for i in range(len(df3["essential_Keywords"])):
        for word in df3["essential_Keywords"][i]:  
            if word not in item_check_remove_list:                 
                combined_list_essential_Keywords.append(word)                
            else:
                continue           
    
    #getting combined list of Item to check
    combined_list_final=[]
    for i in range(len(df3["item_check_Keywords"])):
        for word in df3["item_check_Keywords"][i]:  
            if word not in item_check_remove_list:                 
                combined_list_final.append(word)                
            else:
                continue
                
    #add a new column of combined essential_Keywords in Observation data frame
    combined_list_essential_Keywords=list(set(combined_list_essential_Keywords))    
    df4["combined_essential_Keywords"]=None
    for i in range(len(df4["combined_essential_Keywords"])):
        df4["combined_essential_Keywords"].iloc[i]=combined_list_essential_Keywords 
        
    #add a new column of combined item to check in Observation data frame
    combined_list_final=list(set(combined_list_final)) 
    combined_list_final = [x for x in combined_list_final if x not in combined_list_essential_Keywords]
    df4["combined_keywords"]=None
    for i in range(len(df4["combined_keywords"])):
        df4["combined_keywords"].iloc[i]=combined_list_final       
    
    nature_check_remove_list=['ai','not','2','reord','note','order','nm','at','use','ic','conn','con','ec','on board','time','low','back up','dr','vt','id','ME','CF','406','cpp','cf','two','name','off','date','s','pi','no go','ink','np232','p','tss','as','sm','pl','two way','key','Off','3 cm','size','each','on','16','x','form c','way','upto','new','near miss','pm','pp','check','3','number','ra','1w','up side','available','s63','np 231','dpa','me','back','in force','good','oow','cm']
    dict_replace_nature_check={"nav warning":"warning","sat c":"sat","notice to mariner":"notice mariner","at sea maintenance":"maintenance"}    #method to remove irrelevant keywords
    #method to remove irrelevant keywords
    def remove_irrelevant_keywords(list_a,list_b):
        temp_list=[]
        for word in list_a:        
                if word not in list_b:
                    temp_list.append(word)
                else:
                    continue
        return list(set(temp_list))
        
    #method to replace keywords
    def replace_method_keywords(list_a,new_dict):    
        for i in range(len(list_a)):
            for key,value in new_dict.items():
                if list_a[i]==key:
                    list_a[i]=value
                else:
                    continue  
        return list(set(list_a))
    df3["essential_Keywords"]=df3.apply(lambda x: remove_irrelevant_keywords(x['essential_Keywords'],item_check_remove_list), axis=1)
    df3["item_check_Keywords"]=df3.apply(lambda x: remove_irrelevant_keywords(x['item_check_Keywords'],item_check_remove_list), axis=1)
    df3["nature_check_Keywords"]=df3.apply(lambda x: remove_irrelevant_keywords(x['nature_check_Keywords'],nature_check_remove_list), axis=1)
    df3["item_check_Keywords"]=df3.apply(lambda x: replace_method_keywords(x['item_check_Keywords'],dict_replace_item_check), axis=1)
    df3["nature_check_Keywords"]=df3.apply(lambda x: replace_method_keywords(x['nature_check_Keywords'],dict_replace_nature_check), axis=1)  
    
    #Method to search the whole phrase
    def search_phrase_sequence(input_string,search_string):
        import re
        list_match=[]
        input_string=input_string.lower()
        search_string=search_string.lower()
        input_string=stemmed_string(input_string)
        search_string=stemmed_string(search_string)
        list_match=re.findall('\\b'+search_string+'\\b',input_string)
        if list_match!=[]:
            return True
        else:
            return False   
    #Method to match whole word from given sentence
    def find_only_whole_word(input_string,search_string):
        '''Method which will return True or False when searching key is available'''
        # Create a raw string with word boundaries from the user's input_string
        search_string=search_string.lower()
        input_string=input_string.lower()
        search_string=stemmed_string(search_string)
        input_string=stemmed_string(input_string) 
        list_string=list()
        list_string2=list()
        word_list=[]
        str_keyword = " "
        list_string2=search_string.split(" ")     
        list_string=input_string.split(" ")
        for word1 in list_string:
            for word2 in list_string2:
                if word1==word2:
                    word_list.append(word2)
                    word_list=list(set(word_list))
                else:
                    continue
        # traverse in the string
        for x in word_list:
            str_keyword += x + ' '    
        str_keyword=str_keyword.strip()    
        str_keyword_list=str_keyword.split()
        if str_keyword!=" " and (len(str_keyword_list)==len(list_string2)):
            return True
        else:
            return False
            
    # method to return list of exact matched string from given argument
    def filter_list_string_essential_keywords(list_a,list_b):
        '''method to return list of matched string from given argument'''
        list_new=[]
        for str1 in list_a:
            for str2 in list_b:
                if search_phrase_sequence(str1,str2):
                    list_new.append(str2)
                else:
                    continue
        return list(set(list_new))
    
    #Filter the keyword from item to check from reference checklist
    df4['filtered_keywords'] = df4.apply(lambda x: filter_list_string_essential_keywords(x['parsed_keywords'], x['combined_essential_Keywords']), axis=1)

    # method to return list of matched string from given argument
    def filter_list_string(list_a,list_b):
        '''method to return list of matched string from given argument'''
        list_new=[]
        for str1 in list_a:
            for str2 in list_b:
                if find_only_whole_word(str1,str2):
                    list_new.append(str2)
                else:
                    continue
        return list(set(list_new))  
        
    #Find matched list when essential_Keywords list match is empty  
    for i in range(len(df4['filtered_keywords'])):
        if df4['filtered_keywords'][i]==[]:
            df4['filtered_keywords'] = df4.apply(lambda x: filter_list_string(x['parsed_keywords'], x['combined_keywords']), axis=1)
        else:
            continue

    #method to find sub string in given two strings having length greater then one
    def method_to_find_substring_extra_keyword(input_string,search_string):
        '''method to find sub string in given two strings having length greater then one'''
        # importing modules 
        from nltk.stem import PorterStemmer 
        from nltk.tokenize import word_tokenize 
        import re
        ps = PorterStemmer()
        input_string=input_string.lower()
        search_string=search_string.lower()
        input_string=stemmed_string(input_string)
        search_string=stemmed_string(search_string) 
        list_string=[]
        list_string2=[]
        str_keyword = " "
        list_split_string=input_string.split(" ") 
        list_split_string2=search_string.split(" ")
        for word1 in list_split_string:
            for word2 in list_split_string2:
                if word1==word2:
                    list_string.append(word2)
                    list_string=list(set(list_string))
                else:
                    continue
        # traverse in the string
        for x in list_string:
            str_keyword += x + ' '    
        str_keyword=str_keyword.strip()    
        str_keyword_list=str_keyword.split()
        if str_keyword!=" " and (len(str_keyword_list)==len(list_split_string2)):
            list_string2.append(search_string)
            list_string2.append(str_keyword)  
            return list_string2
        else:
            list_string2.append("no match")
            list_string2.append("no match")
            return list_string2
            
    #method to return new filtered list by applying new matching method
    def find_new_filtered_list(list_a,list_b):
        '''method to return new filtered list by applying new matching method'''
        new_filtered_list=[]
        for i in range(len(list_a)):
            for j in range(len(list_b)):
                temp=method_to_find_substring_extra_keyword(list_a[i],list_b[j])  
                if temp[0]!="no match":
                    new_filtered_list.append(temp[0])                
                else:
                    continue               
        return new_filtered_list
    #method to return list of matched string in reverse order
    def filter_list_string_reverse_order(list_a,list_b):
        '''method to return list of matched string in reverse order'''
        list_new=[]
        for str1 in list_a:
            for str2 in list_b:
                if find_only_whole_word(str1,str2):
                    list_new.append(str2)
                else:
                    continue
        return list(set(list_new))

    #method to return new filtered list in reverse order by applying new matching method with Item to check column for Reference 
    #check list sheet
    def find_new_filtered_list_reverse_order(list_a,list_b):
        '''#method to return new filtered list in reverse order by applying new matching method with Item to check column for Reference 
    #check list sheet'''
        new_filtered_list=[]
        new_matched_list=[]
        for i in range(len(list_a)):
            for j in range(len(list_b)):
                temp=method_to_find_substring_extra_keyword(list_a[i],list_b[j])  
                if temp[0]!="no match":
                    new_filtered_list.append(temp[0])
                    new_matched_list.append(temp[1])
                else:
                    continue
        #new_filtered_list=filter_list_string_reverse_order(new_filtered_list,combined_list_final)        
        return [new_filtered_list,new_matched_list]

    #filling empty value in filtered list by applying new filtered reverse order method
    for i in range(len(df4["filtered_keywords"])):
        if df4["filtered_keywords"][i]==[]:
            df4["filtered_keywords"][i]=(find_new_filtered_list_reverse_order(df4["parsed_keywords"][i],df4["combined_keywords"][i]))[0]                   
        else:
            continue 

    #method to create list array by searching keywords in item to check of reference checklist
    def search_keyword_create_list_of_index(keyword_list):  
        '''method to create list array by searching keywords in item to check of reference checklist'''
        index_list=[]
        for word in keyword_list:
            for i in range(len(df3["item_check_Keywords"])):
                for j in range(len(df3["item_check_Keywords"][i])):
                    text1=str(word).lower()
                    text2=str(df3["item_check_Keywords"][i][j]).lower()
                    if text1==text2:
                        index_list.append(i)
                    else:
                        continue
        return list(set(index_list))
    #Creating an index list column by searching it in item to check of reference checklist
    df4["index_list"]=df4["filtered_keywords"].apply(search_keyword_create_list_of_index)   
    #creating a new dataframe
    df_PVSN=pd.DataFrame(columns=["parsed_keywords","VIQ_No","Sub_VIQ_NO","nature_check_Keywords"])
    #converting index list datatypes into integer type
    df4["index_list"]=df4["index_list"].apply(pd.to_numeric)
    #concatenating dataframe
    k=0
    for i in range(len(df4["index_list"])):        
            for val in df4["index_list"][i]:            
                df_PVSN.loc[k]=[df4["parsed_keywords"][i],df3["VIQ_No"][val],df3["Sub_VIQ_NO"][val],df3["nature_check_Keywords"][val]]
                k+=1  

    #Method to return list of VIQ and Sub VIQ after first pass
    def method_return_VIQ_first_pass(df): 
        VIQ_SUBVIQ_First_list=list()
        for i in range(len(df["parsed_keywords"])):   
            temp=None
            temp_list=list()
            temp=df[["VIQ_No","Sub_VIQ_NO"]].iloc[i]
            temp_list=[temp["VIQ_No"],temp["Sub_VIQ_NO"]]
            VIQ_SUBVIQ_First_list.append(temp_list)
        return VIQ_SUBVIQ_First_list        
    
    #creating a new column and assign value into null
    df_PVSN["matched_list"]=None

    #method to return new filtered list in reverse order by applying new matching method with Item to check column for Reference 
    #check list sheet
    def find_new_filtered_list_nature_check(list_a,list_b):
        '''#method to return matched list applying new matching method with nature of check column for Reference 
    check list sheet'''    
        new_matched_list=[]
        for i in range(len(list_a)):
            for j in range(len(list_b)):
                temp=list()
                temp=method_to_find_substring_extra_keyword(list_a[i],list_b[j])  
                if temp[0]!="no match":
                    new_matched_list.append(temp[0])                
                else:
                    continue           
        return new_matched_list
    #creating a matched list of second pass
    for i in range(len(df_PVSN["nature_check_Keywords"])):
        temp1=list()
        temp1=find_new_filtered_list_nature_check(df_PVSN["parsed_keywords"].iloc[i],df_PVSN["nature_check_Keywords"].iloc[i]) 
        df_PVSN["matched_list"].iloc[i]=temp1    
    #Creating new column of list of VIQ and Sub_Viq number from Reference check list 
    def method_return_VIQ_second_pass(df):
        VIQ_SUBVIQ_list=list()    
        for i in range(len(df)):        
            for val in df["matched_list"][i]:
                if len(val)!=0:
                    temp=None
                    temp_list=list()
                    temp=df[["VIQ_No","Sub_VIQ_NO"]].iloc[i]
                    temp_list=[temp["VIQ_No"],temp["Sub_VIQ_NO"]]
                    VIQ_SUBVIQ_list.append(temp_list)
                else:
                    continue
        VIQ_SUBVIQ_list = [list(x) for x in set(tuple(x) for x in VIQ_SUBVIQ_list)]
        return VIQ_SUBVIQ_list
    #Getting VIQ and sub viq list after second pass
    VIQ_SUBVIQ_list_1st=method_return_VIQ_first_pass(df_PVSN)
    VIQ_SUBVIQ_list_2nd=method_return_VIQ_second_pass(df_PVSN)
    final_list=list()
    #return ("List from First Pass:-> ",[list(VIQ_SUBVIQ_list_1st)],"List From Second pass is:->",[list(VIQ_SUBVIQ_list_2nd)])
    if len(VIQ_SUBVIQ_list_2nd)==0:
        final_list=VIQ_SUBVIQ_list_1st
    else:
        final_list=VIQ_SUBVIQ_list_2nd
    return final_list  


