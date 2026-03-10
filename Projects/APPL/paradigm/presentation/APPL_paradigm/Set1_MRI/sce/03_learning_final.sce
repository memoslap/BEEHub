scenario = "fMRI-SET-1";     																								  
default_background_color = 0, 0, 0;
active_buttons = 2;
button_codes = 1,2;  	#1 Pfeil nach links=richtig,2 Pfeil nach rechts =falsch; 3= Leertaste ; 4-6= Tastatur 1,2,3
target_button_codes = 1,2;
#write_codes = true;
response_matching = simple_matching;
event_code_delimiter = ",";
#pulse_width = 10;

# fMRT
#scenario_type = fMRI_emulation;
#scan_period = 4500;

scenario_type = fMRI;
pulses_per_scan = 1;
scan_period = 1000;
pulse_code = 30;
pulse_width = 6; 

begin;

bitmap { filename = ""; width = 600; height = 600; preload = false; } presPic;
bitmap { filename = ""; width = 600; height = 398; preload = false; } infoPic;
text { system_memory = true; font_color = 255, 255, 255; transparent_color = 0,0,0;	font_size = 100;caption = "...";} presWord;

################### STIMULUS TRIAL ###################################
trial {
	#trial_type = first_response;
	stimulus_event {
      picture { 
         bitmap presPic; #picture
			x = 0; y = 0; 
         text presWord; 
			x = 0; y = -400; 
         } picStim;
			time = 0;
		}stimEvent;
	#stimulus_event {
	#	picture { 
	#		text {
	#		system_memory = true;
	#		font_color = 255, 255, 255;
	#		font_size = 100;
	#		caption = "-";
	#	} respText;
	#	x = 0; y = 0;
	#	
	#	}picStim2;
	#	time = 2500;
	#	}stimEvent2;

}StimTrial;

################### FEEDBACK TRIAL ###################################
trial {
	
	stimulus_event {
		picture { 
			text {
			system_memory = true;
			font_color = 255, 255, 255;
			font_size = 100;
			caption = "-";
		} FeedText;
		x = 0; y = 0;
		}feedPic;
		time = 0;
		}FeedEvent;

}FeedTrial;


trial {
	picture { 
		text {
		system_memory = true;
		font_color = 255, 255, 255;
		font_size = 100;
		caption = "+";
		} fixText;
		x = 0; y = 0;	
		}fixStim;
		time = 0;
		code = "fix";
}fixTrial;

trial {
	stimulus_event {
      picture { 
         bitmap infoPic; #picture
			x = 0; y = 0; 
         };
			time = 0;
		}InfoEvent;
}InfoTrial;

begin_pcl;

int pulse = 4;

###Change: element number from 5 to 7 and block 5 & 6 commented
array<string> hlcb[4] = {"bubbles/hello.jpg",
								"bubbles/learning.jpg",
								"bubbles/control.jpg",
								"bubbles/bye.jpg"};


array<string> LEARNINGpics1[7] = {"learning/PICTURE_692.jpg",
											"learning/PICTURE_640.jpg",
											"learning/PICTURE_379.jpg",
											"learning/PICTURE_465.jpg",
											"learning/PICTURE_148.jpg",
											"learning/PICTURE_453.jpg",
											"learning/PICTURE_592.jpg"};
LEARNINGpics1.shuffle();											
											
array<string> LEARNINGpics2[7] ={"learning/PICTURE_26.jpg",
											"learning/PICTURE_212.jpg",
											"learning/PICTURE_38.jpg",
											"learning/PICTURE_654.jpg",
											"learning/PICTURE_165.jpg",
											"learning/PICTURE_358.jpg",
											"learning/PICTURE_659.jpg"};
LEARNINGpics2.shuffle();

array<string> LEARNINGpics3[7] = {"learning/PICTURE_67.jpg",
											"learning/PICTURE_68.jpg",
											"learning/PICTURE_71.jpg",
											"learning/PICTURE_72.jpg",
											"learning/PICTURE_202.jpg",
											"learning/PICTURE_203.jpg",
											"learning/PICTURE_74.jpg"};
LEARNINGpics3.shuffle();
											
array<string> LEARNINGpics4[7] = {"learning/PICTURE_77.jpg",
											"learning/PICTURE_267.jpg",
											"learning/PICTURE_97.jpg",
											"learning/PICTURE_100.jpg",
											"learning/PICTURE_224.jpg",
											"learning/PICTURE_566.jpg",
											"learning/PICTURE_32.jpg"};
LEARNINGpics4.shuffle();
											
#array<string> LEARNINGpics5[5] = {"learning/PICTURE_148.jpg",
#											"learning/PICTURE_453.jpg",
#											"learning/PICTURE_165.jpg",
#											"learning/PICTURE_358.jpg",
#											"learning/PICTURE_202.jpg"};
#LEARNINGpics5.shuffle();				
#							
#array<string> LEARNINGpics6[5] = {"learning/PICTURE_203.jpg",
#											"learning/PICTURE_224.jpg",
#											"learning/PICTURE_566.jpg",
#											"learning/PICTURE_414.jpg",
#											"learning/PICTURE_42.jpg"};
#LEARNINGpics6.shuffle();

###Change: Element number from 5 to 7 and block 5 & 6 commented
array<string> LEARNINGwords1[7][5] = {{"Halne","Halpe","Haler","Halge","Halser"},
											{"Letim","Lemet","Legas","Letar","Leniel"},
											{"Larbe","Largas","Lartan","Larnel","Lartum"},
											{"Flister","Flistan","Flistun","Flisber","Flistert"},
											{"Schiehel","Schiegun","Schiemer","Schieton","Schieter"},
											{"Neffit","Neffsen","Neffgasch","Neffser","Nefftoll"},
											{"Helte","Heltaun","Helsal","Helger","Helgu"}};
LEARNINGwords1.shuffle();											
											
array<string> LEARNINGwords2[7][5] = {{"Logatt","Lose","Lonap","Lomack","Lomant"},
											{"Limtepp","Limnap","Limrest","Limmant","Limpad"},
											{"Derlas","Derpest","Dervat","Derpod","Derdum"},
											{"Dobul","Dovat","Dostal","Dodem","Dosir"},
											{"Nehal","Negan","Nerel","Netoll","Nereik"},
											{"Sprünte","Spründent","Sprünlas","Sprüntinn","Sprüntot"},
											{"Dertin","Derstal","Derse","Dersir","Dernark"}};
LEARNINGwords2.shuffle();
											
array<string> LEARNINGwords3[7][5] = {{"Maspe","Mashun","Masles","Mastes","Mastem"},
											{"Hiten","Hine","Hinsin","Hiter","Hitel"},
											{"Melant","Mesin","Metel","Metes","Medost"},
											{"Bleine","Bleitem","Bleites","Bleidos","Bleigo"},
											{"Flofe","Flola","Flogun","Floto","Flolei"},
											{"Wumze","Wumges","Wumes","Wumtik","Wumke"},
											{"Hamen","Hante","Haschin","Hagem","Hages"}};
LEARNINGwords3.shuffle();											
											
array<string> LEARNINGwords4[7][5] = {{"Zase","Zatei","Zatol","Zagon","Zadit"},
											{"Zalbem","Zaldot","Zalkam","Zaldit","Zalme"},
											{"Zepa","Zeka","Zeche","Zelan","Zegat"},
											{"Tirsen","Tirge","Tirpa","Tirgat","Tirdan"},
											{"Herkun","Hertes","Hermo","Hertuk","Herlat"},
											{"Nerkanf","Nermi","Nertil","Nerbat","Nersal"},
											{"Dieges","Diedap","Diestei","Diedam","Diegons"}};
LEARNINGwords4.shuffle();																	
											
#array<string> LEARNINGwords5[5][5] = {{"Schiehel","Nergunt","Flehsen","Schlille","Sasser"},
#											{"Neffit","Flehsen","Negasch","Sasser","Flutoll"},
#											{"Nehel","Negasch","Fohreng","Flutoll","Stinnreik"},
#											{"Sprünte","Fohreng","Ferlas","Stinnreik","Saptot"},
#											{"Flofe","Ferlas","Nergunt","Saptot","Schlille"}};
#LEARNINGwords5.shuffle();
#											
#array<string> LEARNINGwords6[5][5] = {{"Wumze","Fugas","Weetes","Nagif","Harimuk"},
#											{"Herkun","Weetes","Furmi","Harimuk","Nazat"},
#											{"Nerkanf","Furmi","Heutil","Nazat","Ningkal"},
#											{"Wonge","Heutil","Najom","Ningkal","Fastrum"},
#											{"Figat","Najom","Fugas","Fastrum","Nakif"}};
#LEARNINGwords6.shuffle();

###Change: Element number from [30][6] decreased to [28][8]. From i>5 to i>7 and block 5 & 6 commented
array<string> LEARNING[28][8];

loop int i=1 until i>7
begin
	LEARNING[i][1] = LEARNINGpics1[i];
	LEARNING[i][2] = LEARNINGwords1[i][1];
	LEARNING[i][3] = LEARNINGwords1[i][2];
	LEARNING[i][4] = LEARNINGwords1[i][3];
	LEARNING[i][5] = LEARNINGwords1[i][4];
	LEARNING[i][6] = LEARNINGwords1[i][5];
	
	LEARNING[i+7][1] = LEARNINGpics2[i];
	LEARNING[i+7][2] = LEARNINGwords2[i][1];
	LEARNING[i+7][3] = LEARNINGwords2[i][2];
	LEARNING[i+7][4] = LEARNINGwords2[i][3];
	LEARNING[i+7][5] = LEARNINGwords2[i][4];
	LEARNING[i+7][6] = LEARNINGwords2[i][5];
	
	LEARNING[i+14][1] = LEARNINGpics3[i];
	LEARNING[i+14][2] = LEARNINGwords3[i][1];
	LEARNING[i+14][3] = LEARNINGwords3[i][2];
	LEARNING[i+14][4] = LEARNINGwords3[i][3];
	LEARNING[i+14][5] = LEARNINGwords3[i][4];
	LEARNING[i+14][6] = LEARNINGwords3[i][5];
	
	LEARNING[i+21][1] = LEARNINGpics4[i];
	LEARNING[i+21][2] = LEARNINGwords4[i][1];
	LEARNING[i+21][3] = LEARNINGwords4[i][2];
	LEARNING[i+21][4] = LEARNINGwords4[i][3];
	LEARNING[i+21][5] = LEARNINGwords4[i][4];
	LEARNING[i+21][6] = LEARNINGwords4[i][5];
	
	#LEARNING[i+20][1] = LEARNINGpics5[i];
	#LEARNING[i+20][2] = LEARNINGwords5[i][1];
	#LEARNING[i+20][3] = LEARNINGwords5[i][2];
	#LEARNING[i+20][4] = LEARNINGwords5[i][3];
	#LEARNING[i+20][5] = LEARNINGwords5[i][4];
	#LEARNING[i+20][6] = LEARNINGwords5[i][5];
	
	#LEARNING[i+25][1] = LEARNINGpics6[i];
	#LEARNING[i+25][2] = LEARNINGwords6[i][1];
	#LEARNING[i+25][3] = LEARNINGwords6[i][2];
	#LEARNING[i+25][4] = LEARNINGwords6[i][3];
	#LEARNING[i+25][5] = LEARNINGwords6[i][4];
	#LEARNING[i+25][6] = LEARNINGwords6[i][5];
	
	i = i + 1;
	
end;

#CHECK!!!!
###Change: 5 & 6 commented
loop int i=1 until i>LEARNING.count()
begin
	term.print_line(LEARNING[i][1] + " - " + LEARNING[i][2] + " - " + LEARNING[i][3] + " - " + LEARNING[i][4]); #+ " - " + LEARNING[i][5] + " - " + LEARNING[i][6]);
	i = i + 1;
end;



# Load Trials
# 1 Learning Trials
# allPics[Picture, corrW, incorrW1, incorrW2, incorrW3, incorrW4] 
#array<string> LEARNING[30][6] = {{"learning/PICTURE_559.jpg","hiser","Leniel","Aschdel","Aglud","Letim"},
#											{"learning/PICTURE_640.jpg","geiten","Aschdel","Asir","Letim","Debal"},
#											{"learning/PICTURE_379.jpg","Flofe","Asir","Delgons","Debal","Libtrum"},
#											{"learning/PICTURE_465.jpg","geward","Delgons","Blastaun","Libtrum","Liegast"},
#											{"learning/PICTURE_592.jpg","mummbant","Blastaun","Leniel","Liegast","Aglud"},
#											{"learning/PICTURE_26.jpg","flister","Bogast","Letmap","Limjepp","Limmant"},
#   										{"learning/PICTURE_212.jpg","gluktant","Letmap","Deflas","Limmant","Lispad"},
#   										{"learning/PICTURE_38.jpg","helte","Deflas","Basut","Lispad","Logatt"},
#											{"learning/PICTURE_654.jpg","hürtem","Basut","Derbstal","Logatt","Logas"},
#											{"learning/PICTURE_659.jpg","schiehel","Derbstal","Bogast","Logas","Limjepp"},
#											{"learning/PICTURE_67.jpg","eume","Merschink","Dobast","Lokrast","Nazehl"},
#											{"learning/PICTURE_68.jpg","habel","Dobast","Dobul","Nazehl","Luttes"},
#											{"learning/PICTURE_71.jpg","enkor","Dobul","Fastrum","Luttes","Meidost"},
#											{"learning/PICTURE_72.jpg","bleine","Fastrum","Eidet","Meidost","Melant"},
#											{"learning/PICTURE_74.jpg","goser","Eidet","Merschink","Melant","Lokrast"},
#					   					{"learning/PICTURE_77.jpg","pase","Fastei","Duckel","Dieges","Fedit"},
#											{"learning/PICTURE_267.jpg","wonge","Duckel","Misal","Fedit","Molan"},
#											{"learning/PICTURE_97.jpg","dartin","Misal","Nakif","Molan","Najom"},
#											{"learning/PICTURE_100.jpg","tipnen","Nakif","Ferlas","Najom","Ferdat"},
#											{"learning/PICTURE_32.jpg","tummhaft","Ferlas","Fastei","Ferdat","Dieges"},
#											{"learning/PICTURE_148.jpg","pase","Nergunt","Flehsen","Lumack","Neffit"},
#											{"learning/PICTURE_156.jpg","sporkel","Flehsen","Negasch","Neffit","Flutoll"},
#											{"learning/PICTURE_165.jpg","stinnreik","Negasch","Fohreng","Flutoll","Nehal"},
#											{"learning/PICTURE_358.jpg","sprünte","Fohreng","Froltan","Nehal","Saptot"},
#											{"learning/PICTURE_202.jpg","larbe","Froltan","Nergunt","Saptot","Lumack"},
#											{"learning/PICTURE_203.jpg","wumze","Fugas","Gnatosch","Figat","Nerkanf"},
#											{"learning/PICTURE_224.jpg","furmi","Gnatosch","Harkun","Nerkanf","Jaloss"},
#											{"learning/PICTURE_566.jpg","lomig","Harkun","Heutil","Jaloss","Ningkal"},
#											{"learning/PICTURE_414.jpg","zabem","Heutil","Igat","Ningkal","Pafau"},
#											{"learning/PICTURE_245.jpg","mobe","Igat","Fugas","Pafau","Figat"}};

###Change: Element number from 20 to 28
array<string> CONTROL[28][4] =  {{"control/PICTURE_255.jpg","Schaufel","Fächer","Kette"},
											{"control/PICTURE_551.jpg","Kürbis","Schaufel","Affe"},
											{"control/PICTURE_368.jpg","Fächer","Kette","Kürbis"},
											{"control/PICTURE_708.jpg","Affe","Kürbis","Fächer"},
											{"control/PICTURE_391.jpg","Kette","Affe","Schaufel"},
											{"control/PICTURE_185.jpg","Fussball","Lenkrad","Truthahn"},
											{"control/PICTURE_398.jpg","Lenkrad","Truthahn","Geschenk"},
											{"control/PICTURE_19.jpg","Truthahn","Geschenk","Flasche"},
											{"control/PICTURE_338.jpg","Geschenk","Flasche","Lenkrad"},
											{"control/PICTURE_414.jpg","Lampe","Brille","Birne"},
											{"control/PICTURE_733.jpg","Brille","Birne","Bluse"},
											{"control/PICTURE_42.jpg","Birne","Bluse","Lampe"},
											{"control/PICTURE_59.jpg","Bluse","Lampe","Brille"},
											{"control/PICTURE_343.jpg","Flasche","Fussball","Truthahn"},
											{"control/PICTURE_491.jpg","Teppich","Drache","Feuer"},
											{"control/PICTURE_111.jpg","Drache","Feuer","Walnuss"},
											{"control/PICTURE_116.jpg","Feuer","Walnuss","Anzug"},
											{"control/PICTURE_119.jpg","Walnuss","Anzug","Teppich"},
											{"control/PICTURE_135.jpg","Anzug","Teppich","Drache"},
											{"control/PICTURE_151.jpg","Tablett","Leuchtturm","Teller"},
											{"control/PICTURE_540.jpg","Leuchtturm","Teller","Hase"},
											{"control/PICTURE_234.jpg","Teller","Hase","Panzer"},
											{"control/PICTURE_263.jpg","Hase","Panzer","Tablett"},
											{"control/PICTURE_130.jpg","Weste","Absatz","Zirkel"},
											{"control/PICTURE_266.jpg","Absatz","Zirkel","Butter"},
											{"control/PICTURE_197.jpg","Zirkel","Butter","Weste"},
											{"control/PICTURE_335.jpg","Butter","Weste","Absatz"},
											{"control/PICTURE_621.jpg","Panzer","Tablett","Leuchtturm"}
};

# [Trial, LS]
###Change: trial from 10 to 14 and 5 & 6 commented. ctrll 20 to 28
array<string> blk1[14][4];
array<string> blk2[14][4];
array<string> blk3[14][4];
array<string> blk4[14][4];
#array<string> blk5[14][4];
#array<string> blk6[14][4];

array<string> ctrl1[28][4];
array<string> ctrl2[28][4];

int a = 1;
int b = 1;
int c = 1;
int d = 1;
int e = 1;
int f = 1;

###Change: trial from 40 to 42
# dict. with all correct pairs
array<string> allCorrPairs[42][2];

#int picNum = get_directory_files("C:/Users/malinowskir/Desktop/Marcus/A/Stimuli",  allPics );

##### extra Function please no Questions

sub string getRightName(string pic)
begin
	loop int i = 1 until i > 42
	begin
		if pic == allCorrPairs[i][1] then
			
			return allCorrPairs[i][2];
		end;
	i = i + 1;
	end;

	return "-1";
	
end;

#Make Blocks
###change: element number adjusted e.g. (i<=5) to (i<=7). 5 < 6 blocks commented
loop int i = 1 until i > LEARNING.count()
	begin
		if (i<=7) then	# Block 1
			# learning 1
			blk1[a][1] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";		   #correct [pic,presWORD, corrWORD]
			blk1[a+1][1] = LEARNING[i][1] + ";" + LEARNING[i][3] + ";" + LEARNING[i][2] + ";i";		#incorrect [pic,presWORD, corrWORD]
			# learning 2
			blk1[a][2] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk1[a+1][2] = LEARNING[i][1] + ";" + LEARNING[i][4] + ";" + LEARNING[i][2] + ";i";
			# learning 3
			blk1[a][3]  = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk1[a+1][3] = LEARNING[i][1] + ";" + LEARNING[i][5] + ";" + LEARNING[i][2] + ";i";
			# learning 4
			blk1[a][4] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk1[a+1][4] = LEARNING[i][1] + ";" + LEARNING[i][6] + ";" + LEARNING[i][2] + ";i";
			a = a + 2;
		elseif(i>7) && (i<=14) then	# Block 2
			# learning 1
			blk2[b][1] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk2[b+1][1] = LEARNING[i][1] + ";" + LEARNING[i][3] + ";" + LEARNING[i][2] + ";i";
			# learning 2
			blk2[b][2] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk2[b+1][2] = LEARNING[i][1] + ";" + LEARNING[i][4] + ";" + LEARNING[i][2] + ";i";
			# learning 3
			blk2[b][3] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk2[b+1][3] = LEARNING[i][1] + ";" + LEARNING[i][5] + ";" + LEARNING[i][2] + ";i";
			# learning 4
			blk2[b][4] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk2[b+1][4] = LEARNING[i][1] + ";" + LEARNING[i][6] + ";" + LEARNING[i][2] + ";i";
			b = b + 2;
		elseif(i>14) && (i<=21) then	# Block 3
			# learning 1
			blk3[c][1] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk3[c+1][1] = LEARNING[i][1] + ";" + LEARNING[i][3] + ";" + LEARNING[i][2] + ";i";
			# learning 2
			blk3[c][2] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk3[c+1][2] = LEARNING[i][1] + ";" + LEARNING[i][4] + ";" + LEARNING[i][2] + ";i";
			# learning 3
			blk3[c][3] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk3[c+1][3] = LEARNING[i][1] + ";" + LEARNING[i][5] + ";" + LEARNING[i][2] + ";i";
			# learning 4
			blk3[c][4] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk3[c+1][4] = LEARNING[i][1] + ";" + LEARNING[i][6] + ";" + LEARNING[i][2] + ";i";
			c = c + 2;	
		elseif(i>21) && (i<=28) then	# Block 4
			# learning 1
			blk4[d][1] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk4[d+1][1] = LEARNING[i][1] + ";" + LEARNING[i][3] + ";" + LEARNING[i][2] + ";i";
			# learning 2
			blk4[d][2] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk4[d+1][2] = LEARNING[i][1] + ";" + LEARNING[i][4] + ";" + LEARNING[i][2] + ";i";
			# learning 3
			blk4[d][3] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk4[d+1][3] = LEARNING[i][1] + ";" + LEARNING[i][5] + ";" + LEARNING[i][2] + ";i";
			# learning 4
			blk4[d][4] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			blk4[d+1][4] = LEARNING[i][1] + ";" + LEARNING[i][6] + ";" + LEARNING[i][2] + ";i";
			d = d + 2;
		#elseif(i>20) && (i<=25) then	# Block 5
			# learning 1
			#blk5[e][1] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			#blk5[e+1][1] = LEARNING[i][1] + ";" + LEARNING[i][3] + ";" + LEARNING[i][2] + ";i";
			# learning 2
			#blk5[e][2] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			#blk5[e+1][2] = LEARNING[i][1] + ";" + LEARNING[i][4] + ";" + LEARNING[i][2] + ";i";
			# learning 3
			#blk5[e][3] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			#blk5[e+1][3] = LEARNING[i][1] + ";" + LEARNING[i][5] + ";" + LEARNING[i][2] + ";i";
			# learning 4
			#blk5[e][4] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			#blk5[e+1][4] = LEARNING[i][1] + ";" + LEARNING[i][6] + ";" + LEARNING[i][2] + ";i";
			#e = e + 2;
		#elseif(i>25) && (i<=30) then	# Block 6
			# learning 1
			#blk6[f][1] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			#blk6[f+1][1] = LEARNING[i][1] + ";" + LEARNING[i][3] + ";" + LEARNING[i][2] + ";i";
			# learning 2
			#blk6[f][2] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			#blk6[f+1][2] = LEARNING[i][1] + ";" + LEARNING[i][4] + ";" + LEARNING[i][2] + ";i";
			# learning 3
			#blk6[f][3] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			#blk6[f+1][3] = LEARNING[i][1] + ";" + LEARNING[i][5] + ";" + LEARNING[i][2] + ";i";
			# learning 4
			#blk6[f][4] = LEARNING[i][1] + ";" + LEARNING[i][2] + ";" + LEARNING[i][2] + ";c";
			#blk6[f+1][4] = LEARNING[i][1] + ";" + LEARNING[i][6] + ";" + LEARNING[i][2] + ";i";
			#f = f + 2;
		end;
		i = i+1;
	end;

a = 1;
b = 1;

###changed: trial from 10 to 14
#CONTROL.shuffle();
loop int i = 1 until i > CONTROL.count() 
begin
	if i<=14 then
		# learning 1
		ctrl1[a][1] = CONTROL[i][1] + ";" + CONTROL[i][2] + ";" + CONTROL[i][2] + ";c";
		ctrl1[a+1][1] = CONTROL[i][1] + ";" + CONTROL[i][3] + ";" + CONTROL[i][2] + ";i";
		# learning 2
		ctrl1[a][2] = CONTROL[i][1] + ";" + CONTROL[i][2]+ ";" + CONTROL[i][2] + ";c";
		ctrl1[a+1][2] = CONTROL[i][1] + ";" + CONTROL[i][4] + ";" + CONTROL[i][2] + ";i";
		# learning 3
		ctrl1[a][3] = CONTROL[i+1][1] + ";" + CONTROL[i+1][2] + ";" + CONTROL[i+1][2] + ";c";
		ctrl1[a+1][3] = CONTROL[i+1][1] + ";" + CONTROL[i+1][3] + ";" + CONTROL[i+1][2] + ";i";
		# learning 4
		ctrl1[a][4] = CONTROL[i+1][1] + ";" + CONTROL[i+1][2] + ";" + CONTROL[i+1][2] + ";c";
		ctrl1[a+1][4] = CONTROL[i+1][1] + ";" + CONTROL[i+1][4] + ";" + CONTROL[i+1][2] + ";i";
		a = a + 2;
		
	else
		# learning 1
		ctrl2[b][1] = CONTROL[i][1] + ";" + CONTROL[i][2] + ";" + CONTROL[i][2] + ";c";
		ctrl2[b+1][1] = CONTROL[i][1] + ";" + CONTROL[i][3] + ";" + CONTROL[i][2] + ";i";
		# learning 2
		ctrl2[b][2] = CONTROL[i][1] + ";" + CONTROL[i][2] + ";" + CONTROL[i][2] + ";c";
		ctrl2[b+1][2] = CONTROL[i][1] + ";" + CONTROL[i][4] + ";" + CONTROL[i][2] + ";i";
		# learning 3
		ctrl2[b][3] = CONTROL[i+1][1] + ";" + CONTROL[i+1][2]+ ";" + CONTROL[i+1][2] + ";c";
		ctrl2[b+1][3] = CONTROL[i+1][1] + ";" + CONTROL[i+1][3] + ";" + CONTROL[i+1][2] + ";i";
		# learning 4
		ctrl2[b][4] = CONTROL[i+1][1] + ";" + CONTROL[i+1][2] + ";" + CONTROL[i+1][2] + ";c";
		ctrl2[b+1][4] = CONTROL[i+1][1] + ";" + CONTROL[i+1][4] + ";" + CONTROL[i+1][2] + ";i";
		b = b + 2;
		
	end;
	i = i + 2;
end;
###changed: blocks from 8 to 6 and trials from 10 t0 14. blk 5 & 6 commented
# Check Trial Train. 
array<int> BlockOrder[] = {1,2,3,4,5,6}; ## 7 = Contro-1 and 8 = Control-2 

array<string> Task_List[6][4][14];

loop int blk = 1 until blk > 6
begin
	loop int ls = 1 until ls > 4
	begin
		loop int item = 1 until item > 14
		begin
			# Blocks
			if blk == 1 then
				Task_List[blk][ls][item] = blk1[item][ls];
			elseif blk == 2 then
				Task_List[blk][ls][item] = blk2[item][ls];
			elseif blk == 3 then
				Task_List[blk][ls][item] = blk3[item][ls];
			elseif blk == 4 then
				Task_List[blk][ls][item] = blk4[item][ls];
			#elseif blk == 5 then
				#Task_List[blk][ls][item] = blk5[item][ls];
			#elseif blk == 6 then
				#Task_List[blk][ls][item] = blk6[item][ls];
			elseif blk == 5 then	#Control-Block
				Task_List[blk][ls][item] = ctrl1[item][ls];
			elseif blk == 6 then #Control-Block
				Task_List[blk][ls][item] = ctrl2[item][ls];
			end;
			item = item + 1;
		end;
		
		## Shuffle lStage Items
		###changed: 10 & 14
		array<string> dummy[14];
		bool isOK = false;
		loop until isOK
		begin
			dummy = Task_List[blk][ls];
			dummy.shuffle();
			Task_List[blk][ls] = dummy;
			loop int k = 1 until k > 13
			begin
				#term.print_line(k);
				#term.print_line(LSpairs[block][lStage][k]);
				#term.print_line(LSpairs[block][lStage][k+1]);
				array<string> N[1];
				array<string> N2[1];
				Task_List[blk][ls][k].split(";",N);
				Task_List[blk][ls][k+1].split(";",N2);	
			
				if N[1] == N2[1] || N[2] == N2[2] || N[3] == N2 [2] then
					#term.print_line("NÖÖÖ");
					isOK = false;
					break;
					
				else
					isOK = true;	
				end;	
			k = k + 1;
			end;
			
		end;
		
		ls = ls + 1;	
		
	end;
	
	blk = blk + 1;
end;



################## write corr Pair-list #######
#string id = logfile.subject();
#id = id + "_corrPair.txt";
#output_file ofile = new output_file;

#ofile.open(id, true); #overwrite true
#int n = 1;
#loop int b = 1 until b > 4
#begin 
#	loop int w=1 until w > 10
#	begin
#	ofile.print(corrWords[b][w] + ";" + corrPics[b][w] + "\n");
#	allCorrPairs[n][1] = corrPics[b][w];
#	allCorrPairs[n][2] = corrWords[b][w];
#	n = n + 1; 
#	w = w + 1;
#end;
#b = b + 1;
#end;
#ofile.close();
###############################################			

# make random order of LEARNING- and CONTROL-Blocks
###changed: block number adjusted
int isOrderOK = 0;
loop until isOrderOK == 1
begin
	BlockOrder.shuffle();
	isOrderOK = 1;
	loop int x = 2 until x > BlockOrder.count()
	begin
		if BlockOrder[1] == 5 || BlockOrder[1] == 6 || BlockOrder[6] == 5 || BlockOrder[6] == 6 || (BlockOrder[x-1] == 5 && BlockOrder[x] == 6) || (BlockOrder[x-1] == 6 && BlockOrder[x] == 5) then
			isOrderOK = 0;
			break;	
		end;
		x = x +1 ;
	end;
end;
#check
loop int i = 1 until i > BlockOrder.count()
begin
	term.print_line(BlockOrder[i]);
	i = i + 1;
end;



##### INTRO
string introText = "Das Experiment\nbeginnt gleich.\n\nZu Erinnerung: \n   Ja = Zeigefinger\n Nein = Daumen";

FeedText.set_caption(introText, true);
FeedEvent.set_event_code("Hello - Intro");
FeedTrial.set_duration(100);
#FeedTrial.set_type(first_response);
FeedTrial.present();

bool firstTrial = true;

#Block 1 to 4
###changed: block number from 8 to 6
loop int blk = 1 until blk > 6
begin
	int currBlk = BlockOrder[blk];
	##############################
	#term.print_line("#####");
	#loop int i = 1 until i > allPairs.count()
	#begin
	#	term.print_line(allPairs[i]);
	#	i = i + 1;
	#end;
	#term.print_line("#####");
	##############################
	
	# Block-Intro
	###############
	###changed: block number adjusted
	string infoBubble = "";
	string infoBubble2 = "";
	bool exit = false;
	if currBlk == 5 || currBlk == 6 then
		infoBubble = hlcb[3];	# Control
	elseif  blk == 6 && (currBlk == 1 || currBlk == 2 || currBlk == 3 || currBlk == 4) then
		infoBubble = hlcb[2];	# learning
		infoBubble2 = hlcb[4];	# bye
		exit = true;
	else
		infoBubble = hlcb[2];	# learning
	end;
	
	#Start with Scanner-Pulse synchr.
	if firstTrial then
		fixTrial.set_mri_pulse(pulse);
		firstTrial = false;
	end;
	
	if !exit then
		## Fix 4 pulses between blocks
		loop f = 1 until f > 4
		begin
			if f <= 3 then
				fixTrial.set_duration(4500);	
				fixTrial.present();
			else
				#fixTrial.set_mri_pulse(pulse);
				InfoTrial.set_duration(4500);	
				infoPic.set_filename(infoBubble);
				infoPic.set_draw_mode(1);
				InfoEvent.set_event_code(infoBubble);
				infoPic.load();
				InfoTrial.present();
			end;
			
			f = f + 1;
		end;
	end;
	
	if exit then
		## Fix 4 pulses between blocks
		loop f = 1 until f > 4
		begin
			if f <= 3 then
				fixTrial.set_duration(4500);	
				fixTrial.present();
			else
				#fixTrial.set_mri_pulse(pulse);
				InfoTrial.set_duration(4500);	
				infoPic.set_filename(infoBubble);
				infoPic.set_draw_mode(1);
				InfoEvent.set_event_code(infoBubble);
				infoPic.load();
				InfoTrial.present();
			end;
			
			f = f + 1;
		end;
	end;
	
	###changed: 10 to 14
	loop int ls = 1 until ls > 4
	begin
		loop int i = 1 until i > 14
		begin
						
			int oldRespCount = response_manager.total_response_count();
			
			array<string> strParts[1];
			Task_List[currBlk][ls][i].split(";",strParts);	
			presPic.set_filename(strParts[1]); 														# set bitmap filename
			presWord.set_caption(strParts[2]);
			stimEvent.set_duration(2500);		
			stimEvent.set_event_code(Task_List[currBlk][ls][i] + ";block"+string(blk)+ ";LS"+ string(ls));
							
			presPic.set_draw_mode(1);
			presPic.load();
			presWord.redraw();
			presWord.load();
			
			##Start with Scanner-Pulse synchr.
			#if firstTrial then
			#	StimTrial.set_mri_pulse(pulse);
			#	firstTrial = false;
			#end;			
			
			StimTrial.present();
			
			# Create Feedback depending on Response
			stimulus_data lastStim = stimulus_manager.last_stimulus_data();
			response_data lastResp = response_manager.last_response_data();
			
			#term.print_line(lastStim.time());
			#term.print_line(lastResp.code());
			#term.print_line(lastResp.time());
			#term.print_line("########");
			FeedTrial.set_duration(2000);
			
			#### need to catch only the first response!
			int CurrRespCount = response_manager.total_response_count();
			int targetResp = oldRespCount + 1;
			term.print_line(string(targetResp));
			if targetResp < CurrRespCount then	
				lastResp = response_manager.get_response_data( targetResp );
			else
				lastResp = response_manager.last_response_data();
			end;
			
			
			
			
			
			# Need to catch for the first trial, if there is no response
			int respCount = response_manager.response_count();
			int resTime = 0;
			#term.print_line(string(respCount));
			if respCount == 0 then
				resTime = lastStim.time()+3000;
			else
				resTime = lastResp.time();
			end;
						
			# Too late or not
			if resTime >lastStim.time() && resTime <= (lastStim.time() + 2500) then
				
				if (strParts[4] == "c"  && lastResp.code() == 1) || (strParts[4] == "i"  && lastResp.code() == 2) then
					FeedText.set_caption("Korrekt, das ist " + strParts[3], true);
					FeedEvent.set_event_code("Korrekt, das ist " + strParts[3]);
					FeedTrial.present();
				else
					# all other
					FeedText.set_caption("Falsch, das ist " + strParts[3], true);
					FeedEvent.set_event_code("Falsch, das ist " + strParts[3]);
					FeedTrial.present();
				end;
							
			else
				
				FeedText.set_caption("Zu spät, das ist " + strParts[3], true);
				FeedEvent.set_event_code("Zu spät, das ist " + strParts[3]);
				FeedTrial.present();
				
			end;
					
		
			pulse = pulse + 1;
								
			i = i+1;
				
		end;
		## Fix between learning stage
		#fixTrial.set_mri_pulse(pulse);
		fixTrial.set_duration(4500);	
		fixTrial.present();
		pulse = pulse + 1;
		ls = ls + 1;
	end;
	
	if exit then
		## Fix 4 pulses between blocks
		loop f = 1 until f > 4
		begin
			if f <= 3 then
				fixTrial.set_duration(4500);	
				fixTrial.present();
			else
				#fixTrial.set_mri_pulse(pulse);
				InfoTrial.set_duration(4500);	
				infoPic.set_filename(infoBubble2); 
				infoPic.set_draw_mode(1);
				infoPic.load();
				InfoTrial.present();
			end;
			
			f = f + 1;
		end;
	end;	
	
	
blk = blk + 1;
end;










