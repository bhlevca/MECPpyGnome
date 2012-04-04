/*
 *  ShioTimeValue_c.cpp
 *  c_gnome
 *
 *  Created by Generic Programmer on 2/24/12.
 *  Copyright 2012 __MyCompanyName__. All rights reserved.
 *
 */

#include "ShioTimeValue_c.h"
#include "CROSS.H"
#include <fstream>
#include <ios>
#include <iostream>
#include <cstdlib>

using namespace std;

#ifdef pyGNOME
#define TOSSMTimeValue OSSMTimeValue_c
#define TechError(a, b, c) printf(a)
#define printError(msg) printf(msg)
#endif

#ifdef pyGNOME
#define abs(n) ((n) >= 0 ? (n) : -(n))
#endif

Boolean DaylightSavingTimeInEffect(DateTimeRec *dateStdTime)
{
	// Assume that the change from standard to daylight
	// savings time is on the first Sunday in April at 0200 and 
	// the switch back to Standard time is on the
	// last Sunday in October at 0200.             
	
	//return false;	// code goes here, outside US don't use daylight savings
#ifndef pyGNOME
	if (settings.daylightSavingsTimeFlag == DAYLIGHTSAVINGSOFF) return false;
#else
	return false;
#endif
	
	switch(dateStdTime->month)
	{
		case 1:
		case 2:
		case 3:
		case 11:
		case 12:
			return false;
			
		case 5:
		case 6:
		case 7:
		case 8:
		case 9:
			return true;
			
		case 4: // april
			if(dateStdTime->day > 7) return true; // past the first week
			if(dateStdTime->dayOfWeek == 1) 
			{	// first sunday
				if(dateStdTime->hour >= 2) return true;  // after 2AM
				else return false; // before 2AM
			}
			else
			{	// not Sunday
				short prevSundayDay = dateStdTime->day - dateStdTime->dayOfWeek + 1;
				if(prevSundayDay >= 1) return true; // previous Sunday was this month, so we are after the magic Sunday
				else return false;// previous Sunday was previous month, so we are before the magic Sunday
			}
			
		case 10://Oct
			if(dateStdTime->day < 25) return true; // before the last week
			if(dateStdTime->dayOfWeek == 1) 
			{	// last sunday
				if(dateStdTime->hour >= 2) return false;  // after 2AM
				else return true; // before 2AM
			}
			else
			{	// not Sunday
				short nextSundayDay = dateStdTime->day - dateStdTime->dayOfWeek + 8;
				if(nextSundayDay > 31) return false; // next Sunday is next month, so we are after the magic Sunday
				else return true;// next Sunday is this month, so we are before the magic Sunday
			}

	}
	return false;// shouldn't get here
}

char* GetKeyedLine(CHARH f, char*key, long lineNum, char *strLine)
{	// copies the next line into strLine
	// and returns ptr to first char after the key
	// returns NIL if key does not match
	char* p = 0;
	long keyLen = strlen(key);
	NthLineInTextOptimized (*f,lineNum, strLine, kMaxKeyedLineLength); 
	RemoveTrailingWhiteSpace(strLine);
	if (!strncmpnocase(strLine,key,keyLen)) 
		p = strLine+keyLen;
	return p;
}


void ShioTimeValue_c::ProgrammerError(char* routine)
{
	char str[256];
	if(routine)  sprintf(str,"Programmer error: can't call %s() for TShioTimeValue objects",routine);
	else sprintf(str,"Programmer error: TShioTimeValue object");
	printError(str);
}

OSErr ShioTimeValue_c::GetKeyedValue(CHARH f, char*key, long lineNum, char* strLine,float *** val)
{
#define kMaxNumVals 100
#define kMaxStrChar 32
	float** h = (float**)_NewHandleClear(kMaxNumVals*sizeof(***val));
	char *p;
	OSErr scanErr = 0;
	double value;
	long i,numVals = 0;
	char str[kMaxStrChar];
	OSErr err = 0;
	
	if(!h) return -1;
	
	*val = nil;
	if(!(p = GetKeyedLine(f,key,lineNum,strLine)))  {err = -2; goto done;}
	for(;;) //forever
	{
		str[0] = 0;
		for(;*p == ' ' && *p == '\t';p++){} // move past leading white space
		if(*p == 0) goto done;
		for(i = 0;i < kMaxStrChar && *p != ' ' && *p != '\t' && *p ;str[i++] = (*p++)){} // copy to next white space or end of string
		if(i == kMaxStrChar) {err = -3; goto done;}
		str[i] = 0;
		p++;
		scanErr =  StringToDouble(str,&value);
		if(scanErr) return scanErr;
		(*h)[numVals++] = value;
		if(numVals >= kMaxNumVals) {err = -4; goto done;}
	}
	
done:
	if(numVals < 10) err = -5;// probably a bad line
	if(err && h) {_DisposeHandle((Handle)h); h = 0;}
	else { _SetHandleSize((Handle)h,numVals*sizeof(***val)); }
	*val = h;
	return err;
}


OSErr ShioTimeValue_c::GetKeyedValue(CHARH f, char*key, long lineNum, char* strLine,DATA * val)
{
	char *p,*p2;
	OSErr scanErr = 0;
	double value;
	if(!(p = GetKeyedLine(f,key,lineNum,strLine)))  return -1;
	// find the second part of the string
	for(p2 = p; TRUE ; p2++)
	{//advance to the first space
		if(*p2 == 0) return -1; //error, only one part to the string
		if(*p2 == ' ') 
		{
			*p2 = 0; // null terminate the first part
			p2++;
			break;
		}
	}
	scanErr =  StringToDouble(p,&value);
	if(scanErr) return scanErr;
	val->val = value;
	scanErr =  StringToDouble(p2,&value);
	if(scanErr) return scanErr;
	val->dataAvailFlag = round(value);
	return 0;
}

OSErr ShioTimeValue_c::GetKeyedValue(CHARH f, char*key, long lineNum, char* strLine,short * val)
{
	char *p;
	OSErr scanErr = 0;
	double value;
	if(!(p = GetKeyedLine(f,key,lineNum,strLine)))  return -1;
	scanErr =  StringToDouble(p,&value);
	if(scanErr) return scanErr;
	*val = round(value);
	return 0;
}


OSErr ShioTimeValue_c::GetKeyedValue(CHARH f, char*key, long lineNum, char* strLine,float * val)
{
	char *p;
	OSErr scanErr = 0;
	double value;
	if(!(p = GetKeyedLine(f,key,lineNum,strLine)))  return -1;
	scanErr =  StringToDouble(p,&value);
	if(scanErr) return scanErr;
	*val = value;
	return 0;
}

OSErr ShioTimeValue_c::GetKeyedValue(CHARH f, char*key, long lineNum, char* strLine,double * val)
{
	char *p;
	OSErr scanErr = 0;
	double value;
	if(!(p = GetKeyedLine(f,key,lineNum,strLine)))  return -1;
	scanErr =  StringToDouble(p,&value);
	if(scanErr) return scanErr;
	*val = value;
	return 0;
}

void SplitPathFile(CHARPTR fullPath, CHARPTR fileName);

OSErr ShioTimeValue_c::ReadTimeValues (char *path, short format, short unitsIfKnownInAdvance)
{
	// code goes here, use unitsIfKnownInAdvance to tell if we're coming from a location file, 
	// if not and it's a heights file ask if progressive or standing wave (add new field or track as 'P')
	//#pragma unused(unitsIfKnownInAdvance)	
	char strLine[kMaxKeyedLineLength];
	long i,numValues;
	double value1, value2, magnitude, degrees;
	CHARH f = 0;
	DateTimeRec time;
	TimeValuePair pair;
	OSErr	err = noErr,scanErr;
	long lineNum = 0;
	char *p;
	long numScanned;
	double value;
	CONTROLVAR  DatumControls;
	
	if (err = TOSSMTimeValue::InitTimeFunc()) return err;
	
	timeValues = 0;
	fileName[0] = 0;
	
	if (!path) return -1;
	
	strcpy(strLine, path);
	SplitPathFile(strLine, this->fileName);
	
#ifndef pyGNOME
	
	err = ReadFileContents(TERMINATED, 0, 0, path, 0, 0, &f);
	if(err)	{ TechError("TShioTimeValue::ReadTimeValues()", "ReadFileContents()", 0); return -1; }
	
#else
	
	char c;
	try {
		int x = i = 0;
		std::string *file_contents = new std::string();
		fstream *_ifstream = new fstream(path, ios::in);
		for(; _ifstream->get(c); x++);
		f = _NewHandle(x);
		delete _ifstream;
		_ifstream = new fstream(path, ios::in);
		for(; i < x && _ifstream->get(c); i++)
			DEREFH(f)[i] = c;
		
	} catch(...) {
		
		printError("We are unable to open or read from the shio tides file. \nBreaking from ShioTimeValue_c::ReadTimeValues().");
		err = true;
		goto readError;
	}
	
#endif
	lineNum = 0;
	// first line
	if(!(p = GetKeyedLine(f,"[StationInfo]",lineNum++,strLine)))  goto readError;
	// 2nd line

	if(!(p = GetKeyedLine(f,"Type=",lineNum++,strLine)))  goto readError;

	switch(p[0])
	{
			//case 'c': case 'C': this->fStationType = 'C'; break;
			//case 'h': case 'H': this->fStationType = 'H'; break;
			//case 'p': case 'P': this->fStationType = 'P';	// for now assume progressive waves selected in file, maybe change to user input
		case 'c': case 'C': 
			this->fStationType = 'C'; break;
		case 'h': case 'H': 
			this->fStationType = 'H';
#ifndef pyGNOME
		{
			// if not a location file, Ask user if this is a progressive or standing wave
			// also ask for scale factor here
			/*if (unitsIfKnownInAdvance==kFudgeFlag)
			 {
			 short buttonSelected;
			 buttonSelected  = MULTICHOICEALERT(1690,"The file you selected is a shio heights file. Are you sure you want to treat it as a progressive wave?",TRUE);
			 switch(buttonSelected){
			 case 1:// continue, treat as progressive wave
			 this->fStationType = 'P';
			 break;  
			 case 3: // cancel
			 //return 0;// leave as standing wave?
			 return -1;
			 break;
			 }
			 //printNote("The shio heights file will be treated as a progressive wave file");
			 //this->fStationType = 'P';
			 }*/
			if (unitsIfKnownInAdvance!=-2)	// not a location file
			{
				Boolean bStandingWave = true;
				float scaleFactor = fScaleFactor;
				err = ShioHtsDialog(&bStandingWave,&scaleFactor,mapWindow);
				if (!err)
				{
					if (!bStandingWave) this->fStationType = 'P';
					//this->fScaleFactor = scaleFactor;
				}
			}
		}
#else
			break;
#endif
		case 'p': case 'P': 
			this->fStationType = 'P';	// for now assume progressive waves selected in file, maybe change to user input
			
			//printError("You have selected a SHIO heights file.  Only SHIO current files can be used in GNOME.");
			//return -1;
			break;	// Allow heights files to be read in 9/18/00
		default:	goto readError; 	
	}
	// 3nd line

	if(!(p = GetKeyedLine(f,"Name=",lineNum++,strLine)))  goto readError;

	strncpy(this->fStationName,p,MAXSTATIONNAMELEN);
	this->fStationName[MAXSTATIONNAMELEN-1] = 0;
	// 
	if(err = this->GetKeyedValue(f,"Latitude=",lineNum++,strLine,&this->fLatitude))  goto readError;
	if(err = this->GetKeyedValue(f,"Longitude=",lineNum++,strLine,&this->fLongitude))  goto readError;
	//
	if(!(p = GetKeyedLine(f,"[Constituents]",lineNum++,strLine)))  goto readError;
	// code goes here in version 1.2.7 these lines won't be required for height files, but should still allow old format
	//if(err = this->GetKeyedValue(f,"DatumControls.datum=",lineNum++,strLine,&this->fConstituent.DatumControls.datum))  goto readError;
	if(err = this->GetKeyedValue(f,"DatumControls.datum=",lineNum++,strLine,&this->fConstituent.DatumControls.datum))  
	{
		if(this->fStationType=='h' || this->fStationType=='H')
		{
			lineNum--;	// possibly new Shio output which eliminated the unused datumcontrols for height files
			goto skipDatumControls;
		}
		else
		{
			goto readError;
		}
	}
	if(err = this->GetKeyedValue(f,"DatumControls.FDir=",lineNum++,strLine,&this->fConstituent.DatumControls.FDir))  goto readError;
	if(err = this->GetKeyedValue(f,"DatumControls.EDir=",lineNum++,strLine,&this->fConstituent.DatumControls.EDir))  goto readError;
	if(err = this->GetKeyedValue(f,"DatumControls.L2Flag=",lineNum++,strLine,&this->fConstituent.DatumControls.L2Flag))  goto readError;
	if(err = this->GetKeyedValue(f,"DatumControls.HFlag=",lineNum++,strLine,&this->fConstituent.DatumControls.HFlag))  goto readError;
	if(err = this->GetKeyedValue(f,"DatumControls.RotFlag=",lineNum++,strLine,&this->fConstituent.DatumControls.RotFlag))  goto readError;
	
skipDatumControls:
	if(err = this->GetKeyedValue(f,"H=",lineNum++,strLine,&this->fConstituent.H))  goto readError;
	if(err = this->GetKeyedValue(f,"kPrime=",lineNum++,strLine,&this->fConstituent.kPrime))  goto readError;
	if(!(p = GetKeyedLine(f,"[Offset]",lineNum++,strLine)))  goto readError;
	
	switch(this->fStationType)
	{
		case 'c': case 'C': 
			if(err = this->GetKeyedValue(f,"MinBefFloodTime=",lineNum++,strLine,&this->fCurrentOffset.MinBefFloodTime))  goto readError;
			if(err = this->GetKeyedValue(f,"FloodTime=",lineNum++,strLine,&this->fCurrentOffset.FloodTime))  goto readError;
			if(err = this->GetKeyedValue(f,"MinBefEbbTime=",lineNum++,strLine,&this->fCurrentOffset.MinBefEbbTime))  goto readError;
			if(err = this->GetKeyedValue(f,"EbbTime=",lineNum++,strLine,&this->fCurrentOffset.EbbTime))  goto readError;
			if(err = this->GetKeyedValue(f,"FloodSpdRatio=",lineNum++,strLine,&this->fCurrentOffset.FloodSpdRatio))  goto readError;
			if(err = this->GetKeyedValue(f,"EbbSpdRatio=",lineNum++,strLine,&this->fCurrentOffset.EbbSpdRatio))  goto readError;
			if(err = this->GetKeyedValue(f,"MinBFloodSpd=",lineNum++,strLine,&this->fCurrentOffset.MinBFloodSpd))  goto readError;
			if(err = this->GetKeyedValue(f,"MinBFloodDir=",lineNum++,strLine,&this->fCurrentOffset.MinBFloodDir))  goto readError;
			if(err = this->GetKeyedValue(f,"MaxFloodSpd=",lineNum++,strLine,&this->fCurrentOffset.MaxFloodSpd))  goto readError;
			if(err = this->GetKeyedValue(f,"MaxFloodDir=",lineNum++,strLine,&this->fCurrentOffset.MaxFloodDir))  goto readError;
			if(err = this->GetKeyedValue(f,"MinBEbbSpd=",lineNum++,strLine,&this->fCurrentOffset.MinBEbbSpd))  goto readError;
			if(err = this->GetKeyedValue(f,"MinBEbbDir=",lineNum++,strLine,&this->fCurrentOffset.MinBEbbDir))  goto readError;
			if(err = this->GetKeyedValue(f,"MaxEbbSpd=",lineNum++,strLine,&this->fCurrentOffset.MaxEbbSpd))  goto readError;
			if(err = this->GetKeyedValue(f,"MaxEbbDir=",lineNum++,strLine,&this->fCurrentOffset.MaxEbbDir))  goto readError;
			SetFileType(SHIOCURRENTSFILE);
			break;
		case 'h': case 'H': 
			if(err = this->GetKeyedValue(f,"HighTime=",lineNum++,strLine,&this->fHeightOffset.HighTime))  goto readError;
			if(err = this->GetKeyedValue(f,"LowTime=",lineNum++,strLine,&this->fHeightOffset.LowTime))  goto readError;
			if(err = this->GetKeyedValue(f,"HighHeight_Mult=",lineNum++,strLine,&this->fHeightOffset.HighHeight_Mult))  goto readError;
			if(err = this->GetKeyedValue(f,"HighHeight_Add=",lineNum++,strLine,&this->fHeightOffset.HighHeight_Add))  goto readError;
			if(err = this->GetKeyedValue(f,"LowHeight_Mult=",lineNum++,strLine,&this->fHeightOffset.LowHeight_Mult))  goto readError;
			if(err = this->GetKeyedValue(f,"LowHeight_Add=",lineNum++,strLine,&this->fHeightOffset.LowHeight_Add))  goto readError;
			SetFileType(SHIOHEIGHTSFILE);
			break;
		case 'p': case 'P': 
			if(err = this->GetKeyedValue(f,"HighTime=",lineNum++,strLine,&this->fHeightOffset.HighTime))  goto readError;
			if(err = this->GetKeyedValue(f,"LowTime=",lineNum++,strLine,&this->fHeightOffset.LowTime))  goto readError;
			if(err = this->GetKeyedValue(f,"HighHeight_Mult=",lineNum++,strLine,&this->fHeightOffset.HighHeight_Mult))  goto readError;
			if(err = this->GetKeyedValue(f,"HighHeight_Add=",lineNum++,strLine,&this->fHeightOffset.HighHeight_Add))  goto readError;
			if(err = this->GetKeyedValue(f,"LowHeight_Mult=",lineNum++,strLine,&this->fHeightOffset.LowHeight_Mult))  goto readError;
			if(err = this->GetKeyedValue(f,"LowHeight_Add=",lineNum++,strLine,&this->fHeightOffset.LowHeight_Add))  goto readError;
			SetFileType(PROGRESSIVETIDEFILE);
			break;
	}
	
	//if(f) delete ((*f)-4); return 0; _DisposeHandle((Handle)f); f = nil;
	return 0;
	
readError:
	if(f) _DisposeHandle((Handle)f); f = nil;
	sprintf(strLine,"Error reading SHIO time file %s on line %ld",this->fileName,lineNum);
		printError(strLine);
		this->Dispose();
		return -1;

	Error:
	if(f) _DisposeHandle((Handle)f); f = nil;
	return -1;
	
}

long	ShioTimeValue_c::GetNumEbbFloodValues()
{
 	long numEbbFloodValues = _GetHandleSize((Handle)fEbbFloodDataHdl)/sizeof(**fEbbFloodDataHdl);
	return numEbbFloodValues;
}

long	ShioTimeValue_c::GetNumHighLowValues()
{
 	long numHighLowValues = _GetHandleSize((Handle)fHighLowDataHdl)/sizeof(**fHighLowDataHdl);
	return numHighLowValues;
}

OSErr ShioTimeValue_c::GetTimeValue(Seconds forTime, VelocityRec *value)
{
	OSErr err = 0;
	Boolean needToCompute = true;
#ifndef pyGNOME
	Seconds modelStartTime = model->GetStartTime();
	Seconds modelEndTime = model->GetEndTime();
#else
	Seconds modelStartTime = this->start_time;
	Seconds modelEndTime = this->stop_time;
#endif
	DateTimeRec beginDate, endDate;
	Seconds beginSeconds;
	Boolean daylightSavings;
	YEARDATAHDL		YHdl = 0; 
	
	long numValues = this->GetNumValues();
	// check that to see if the value is in our already computed range
	if(numValues > 0)
	{
		if(INDEXH(this->timeValues, 0).time <= forTime 
		   && forTime <= INDEXH(this->timeValues, numValues-1).time)
		{ // the value is in the computed range
			if (this->fStationType == 'C')	// allow scale factor for 'P' case
				return TOSSMTimeValue::GetTimeValue(forTime,value);
			else if (this->fStationType == 'P')
				return GetProgressiveWaveValue(forTime,value);
			else if (this->fStationType == 'H')
				return GetConvertedHeightValue(forTime,value);
		}
		//this->fScaleFactor = 0;	//if we want to ask for a scale factor for each computed range...
	}
	// else we need to re-compute the values
	this->SetTimeValueHandle(nil);
	
	// calculate the values every hour for the interval containing the model run time
	//SecondsToDate(modelStartTime,&beginDate);
	SecondsToDate(modelStartTime-6*3600,&beginDate);	// for now to handle the new tidal current mover 1/27/04
	beginDate.hour = 0; // Shio expects this to be the start of the day
	beginDate.minute = 0;
	beginDate.second = 0;
	DateToSeconds(&beginDate, &beginSeconds);
	
	SecondsToDate(modelEndTime+24*3600,&endDate);// add one day so that we can truncate to start of the day
	endDate.hour = 0; // Shio expects this to be the start of the day
	endDate.minute = 0;
	endDate.second = 0;
	
	daylightSavings = DaylightSavingTimeInEffect(&beginDate);// code goes here, set the daylight flag
#ifndef pyGNOME
	YHdl = GetYearData(beginDate.year);
	if(!YHdl)  { TechError("TShioTimeValue::GetTimeValue()", "GetYearData()", 0); return -1; }
#else
	YHdl = (yeardatstruct**)NewHandle(1);	
#endif

	if(this->fStationType == 'C')
	{
		// get the currents
		COMPCURRENTS answers ;
		memset(&answers,0,sizeof(answers));
		err = GetTideCurrent(&beginDate,&endDate,
							 &fConstituent,	
							 &fCurrentOffset,		
							 &answers,		// Current-time struc with answers
							 YHdl,
							 daylightSavings,
							 fStationName);
		//model->NewDirtNotification(DIRTY_LIST);// what we display in the list is invalid
		if(!err)
		{
#ifndef pyGNOME
			model->NewDirtNotification(DIRTY_LIST);// what we display in the list is invalid
#endif
			long i,num10MinValues = answers.nPts,numCopied = 0;
			if(num10MinValues > 0 && answers.timeHdl && answers.speedHdl)
			{
				// copy these values into a handle
				TimeValuePairH tvals = (TimeValuePairH)_NewHandle(num10MinValues* sizeof(TimeValuePair));
				if(!tvals) 
				{TechError("ShioTimeValue_c::GetTimeValue()", "GetYearData()", 0); err = memFullErr; goto done_currents;}
				else
				{
					TimeValuePair tvPair;
					for(i = 0; i < num10MinValues; i++)
					{
						if(INDEXH(answers.timeHdl,i).flag == outOfSequenceFlag) continue;// skip this value, code goes here
						if(INDEXH(answers.timeHdl,i).flag == 1) continue;// skip this value, 1 is don't plot flag - junk at beginning or end of data
						// note:timeHdl values are in hrs from start
						tvPair.time = beginSeconds + (long) (INDEXH(answers.timeHdl,i).val*3600); 
						tvPair.value.u = KNOTSTOMETERSPERSEC * INDEXH(answers.speedHdl,i);// convert from knots to m/s
						tvPair.value.v = 0; // not used
						//INDEXH(tvals,i) = tvPair;	
						INDEXH(tvals,numCopied) = tvPair;	// if skip outOfSequence values don't want holes in the handle
						numCopied++;
					}
					_SetHandleSize((Handle)tvals, numCopied* sizeof(TimeValuePair));
					this->SetTimeValueHandle(tvals);
				}
				////// JLM  , try saving the highs and lows for displaying on the left hand side
				{
					
					short	numEbbFloods = answers.numEbbFloods;			// Number of ebb and flood occurrences.								
					double **EbbFloodSpeedsHdl = answers.EbbFloodSpeedsHdl;	// double knots
					EXTFLAG **EbbFloodTimesHdl = answers.EbbFloodTimesHdl;		// double hours, flag=0 means plot
					short			**EbbFloodHdl = answers.EbbFloodHdl;			// 0 -> Min Before Flood.
					// 1 -> Max Flood.
					// 2 -> Min Before Ebb.
					// 3 -> Max Ebb.
					short numToShowUser;
					short i;
					double EbbFloodSpeed;
					EXTFLAG EbbFloodTime;
					short EbbFlood;
					
					
					/*short numEbbFloodSpeeds = 0;
					 short numEbbFloodTimes = 0;
					 short numEbbFlood = 0;
					 double dBugEbbFloodSpeedArray[40];
					 EXTFLAG dBugEbbFloodTimesArray[40];
					 short dBugEbbFloodArray[40];
					 
					 // just double check the size of the handles is what we expect
					 
					 if(EbbFloodSpeedsHdl)
					 numEbbFloodSpeeds = _GetHandleSize((Handle)EbbFloodSpeedsHdl)/sizeof(**EbbFloodSpeedsHdl);
					 
					 if(EbbFloodTimesHdl)
					 numEbbFloodTimes = _GetHandleSize((Handle)EbbFloodTimesHdl)/sizeof(**EbbFloodTimesHdl);
					 
					 if(EbbFloodHdl)
					 numEbbFlood = _GetHandleSize((Handle)EbbFloodHdl)/sizeof(**EbbFloodHdl);
					 
					 if(numEbbFlood == numEbbFloodSpeeds 
					 && numEbbFlood == numEbbFloodTimes
					 )
					 {
					 for(i = 0; i < numEbbFlood && i < 40; i++)
					 {
					 dBugEbbFloodSpeedArray[i] = INDEXH(answers.EbbFloodSpeedsHdl,i);	// double knots
					 dBugEbbFloodTimesArray[i]  = INDEXH(answers.EbbFloodTimesHdl,i);	// double hours, flag=0 means plot
					 dBugEbbFloodArray[i] = INDEXH(answers.EbbFloodHdl,i);			// 0 -> Min Before Flood.
					 // 1 -> Max Flood.
					 // 2 -> Min Before Ebb.
					 // 3 -> Max Ebb.
					 
					 }
					 dBugEbbFloodArray[39] = dBugEbbFloodArray[39]; // just a break point
					 
					 }*/
					
					
					/////////////////////////////////////////////////
					
					// count the number of values we wish to show to the user
					// (we show the user if the plot flag is set)
					numToShowUser = 0;
					if(EbbFloodSpeedsHdl && EbbFloodTimesHdl && EbbFloodHdl)
					{	
						for(i = 0; i < numEbbFloods; i++)
						{
							EbbFloodTime = INDEXH(EbbFloodTimesHdl,i);
							if(EbbFloodTime.flag == 0)
								numToShowUser++;
						}
					}
					
					// now allocate a handle of this size to hold the values for the user
					
					if(fEbbFloodDataHdl) 
					{
						DisposeHandle((Handle)fEbbFloodDataHdl); 
						fEbbFloodDataHdl = 0;
					}
					if(numToShowUser > 0)
					{
						short j;

						fEbbFloodDataHdl = (EbbFloodDataH)_NewHandleClear(sizeof(EbbFloodData)*numToShowUser);
						if(!fEbbFloodDataHdl) {TechError("TShioTimeValue::GetTimeValue()", "_NewHandleClear()", 0); err = memFullErr; if(tvals)DisposeHandle((Handle)tvals); goto done_currents;}
						for(i = 0, j=0; i < numEbbFloods; i++)
						{

							EbbFloodTime = INDEXH(EbbFloodTimesHdl,i);
							EbbFloodSpeed = INDEXH(EbbFloodSpeedsHdl,i);
							EbbFlood = INDEXH(EbbFloodHdl,i);
							if(EbbFloodTime.flag == 0)
							{
								EbbFloodData ebbFloodData;
								ebbFloodData.time = beginSeconds + (long) (EbbFloodTime.val*3600); // value in seconds
								ebbFloodData.speedInKnots = EbbFloodSpeed; // value in knots
								ebbFloodData.type = EbbFlood; // 0 -> Min Before Flood.
								// 1 -> Max Flood.
								// 2 -> Min Before Ebb.
								// 3 -> Max Ebb.
								INDEXH(fEbbFloodDataHdl,j++) = ebbFloodData;
							}
						}
					}					
				}
				/////////////////////////////////////////////////
				
			}
		}
		
	done_currents:
		
		// dispose of GetTideCurrent allocated handles
		CleanUpCompCurrents(&answers);
		if(err) {return err; }
	}
	
	else if (this->fStationType == 'H')
	{	
		// get the heights
		COMPHEIGHTS answers;
		memset(&answers,0,sizeof(answers));
		err = GetTideHeight(&beginDate,&endDate,
							&fConstituent,	
							YHdl,
							fHeightOffset,
							&answers,
							//**minmaxvalhdl, // not used
							//**minmaxtimehdl, // not used
							//nminmax, // not used
							//*cntrlvars, // not used
							daylightSavings);
		
		//model->NewDirtNotification(DIRTY_LIST);// what we display in the list is invalid
		
		if (!err)
		{
#ifndef pyGNOME
			model->NewDirtNotification(DIRTY_LIST);// what we display in the list is invalid
#endif
			long i,num10MinValues = answers.nPts,numCopied = 0;
			if(num10MinValues > 0 && answers.timeHdl && answers.heightHdl)
			{
				// convert the heights into speeds
				TimeValuePairH tvals = (TimeValuePairH)_NewHandle(num10MinValues*sizeof(TimeValuePair));
				if(!tvals) 
				{TechError("TShioTimeValue::GetTimeValue()", "_NewHandle()", 0); err = memFullErr; goto done_heights;}
				else
				{
					// first copy non-flagged values, then do the derivative in a second loop
					// note this data is no longer used
					double **heightHdl = (DOUBLEH)_NewHandle(num10MinValues*sizeof(double));
					TimeValuePair tvPair;
					double deriv;
					for(i = 0; i < num10MinValues; i++)
					{
						if(INDEXH(answers.timeHdl,i).flag == outOfSequenceFlag) continue;// skip this value, code goes here
						if(INDEXH(answers.timeHdl,i).flag == 1) continue;// skip this value, 1 is don't plot flag - junk at beginning or end of data
						// note:timeHdl values are in hrs from start
						tvPair.time = beginSeconds + (long) (INDEXH(answers.timeHdl,i).val*3600); 
						tvPair.value.u = 0; // fill in later
						tvPair.value.v = 0; // not used
						INDEXH(tvals,numCopied) = tvPair;
						INDEXH(heightHdl,numCopied) = INDEXH(answers.heightHdl,i);
						numCopied++;
					}
					_SetHandleSize((Handle)tvals, numCopied*sizeof(TimeValuePair));
					_SetHandleSize((Handle)heightHdl, numCopied*sizeof(double));
					
					long imax = numCopied-1;
					for(i = 0; i < numCopied; i++)
					{					
						if (i>0 && i<imax) 
						{	// temp fudge, need to approx derivative to convert to speed (m/s), 
							// from ft/min (time step is 10 minutes), use centered difference
							// for now use extra 10000 factor to get reasonable values
							// will also need the scale factor, check about out of sequence flag
							deriv = 3048*(INDEXH(heightHdl,i+1)-INDEXH(heightHdl,i-1))/1200.; 
						}
						else if (i==0) 
						{	
							deriv = 3048*(INDEXH(heightHdl,i+1)-INDEXH(heightHdl,i))/600.; 
						}
						else if (i==imax) 
						{	
							deriv = 3048*(INDEXH(heightHdl,i)-INDEXH(heightHdl,i-1))/600.; 
						}
						INDEXH(tvals,i).value.u = deriv;	// option to have standing (deriv) vs progressive wave (no deriv)
					}
					this->SetTimeValueHandle(tvals);
					DisposeHandle((Handle)heightHdl);heightHdl=0;
				}
				////// JLM  , save the highs and lows for displaying on the left hand side
				{
					short	numHighLows = answers.numHighLows;			// Number of high and low tide occurrences.								
					double **HighLowHeightsHdl = answers.HighLowHeightsHdl;	// double feet
					EXTFLAG **HighLowTimesHdl = answers.HighLowTimesHdl;		// double hours, flag=0 means plot
					short			**HighLowHdl = answers.HighLowHdl;			// 0 -> Low Tide.
					// 1 -> High Tide.
					short numToShowUser;
					short i;
					double HighLowHeight;
					EXTFLAG HighLowTime;
					short HighLow;
					
					/////////////////////////////////////////////////
					
					// count the number of values we wish to show to the user
					// (we show the user if the plot flag is set)
					numToShowUser = 0;
					if(HighLowHeightsHdl && HighLowTimesHdl && HighLowHdl)
					{
						for(i = 0; i < numHighLows; i++)
						{
							HighLowTime = INDEXH(HighLowTimesHdl,i);
							if(HighLowTime.flag == 0)
								numToShowUser++;
						}
					}
					
					// now allocate a handle of this size to hold the values for the user
					
					if(fHighLowDataHdl) 
					{
						DisposeHandle((Handle)fHighLowDataHdl); 
						fHighLowDataHdl = 0;
					}
					if(numToShowUser > 0)
					{
						short j;
						fHighLowDataHdl = (HighLowDataH)_NewHandleClear(sizeof(HighLowData)*numToShowUser);
						if(!fHighLowDataHdl) {TechError("TShioTimeValue::GetTimeValue()", "_NewHandleClear()", 0); err = memFullErr; if(tvals)DisposeHandle((Handle)tvals); goto done_heights;}
						for(i = 0, j=0; i < numHighLows; i++)
						{
							HighLowTime = INDEXH(HighLowTimesHdl,i);
							HighLowHeight = INDEXH(HighLowHeightsHdl,i);
							HighLow = INDEXH(HighLowHdl,i);
							
							if(HighLowTime.flag == 0)
							{
								HighLowData highLowData;
								highLowData.time = beginSeconds + (long) (HighLowTime.val*3600); // value in seconds
								highLowData.height = HighLowHeight; // value in feet
								highLowData.type = HighLow; // 0 -> Low Tide.
								// 1 -> High Tide.
								INDEXH(fHighLowDataHdl,j++) = highLowData;
							}
						}
					}
					
				}
				/////////////////////////////////////////////////
			}
		}
		
		/////////////////////////////////////////////////
		// Find derivative
		if(!err)
		{
			long i;
			Boolean valueFound = false;
			Seconds midTime;
			double forHeight, maxMinDeriv, largestDeriv = 0.;
			HighLowData startHighLowData,endHighLowData;
			double scaleFactor;
			char msg[256];
			for( i=0 ; i<this->GetNumHighLowValues()-1; i++) 
			{
				startHighLowData = INDEXH(fHighLowDataHdl, i);
				endHighLowData = INDEXH(fHighLowDataHdl, i+1);
				if (forTime == startHighLowData.time || forTime == this->GetNumHighLowValues()-1)
				{
					(*value).u = 0.;	// derivative is zero at the highs and lows
					(*value).v = 0.;
					valueFound = true;
				}
				if (forTime > startHighLowData.time && forTime < endHighLowData.time && !valueFound)
				{
					(*value).u = GetDeriv(startHighLowData.time, startHighLowData.height, 
										  endHighLowData.time, endHighLowData.height, forTime);
					(*value).v = 0.;
					valueFound = true;
				}
				// find the maxMins for this region...
				midTime = (endHighLowData.time - startHighLowData.time)/2 + startHighLowData.time;
				maxMinDeriv = GetDeriv(startHighLowData.time, startHighLowData.height,
									   endHighLowData.time, endHighLowData.height, midTime);
				// track largest and save all for left hand list, but only do this first time...
				if (abs(maxMinDeriv)>largestDeriv) largestDeriv = abs(maxMinDeriv);
			}		
			/////////////////////////////////////////////////
			// ask for a scale factor if not known from wizard
#ifndef pyGNOME
			sprintf(msg,lfFix("The largest calculated derivative was %.4lf"),largestDeriv);
			strcat(msg, ".  Enter scale factor for heights coefficients file : ");
			if (fScaleFactor==0)
			{
				err = GetScaleFactorFromUser(msg,&scaleFactor);
				if (err) goto done_heights;
				fScaleFactor = scaleFactor;
			}
#endif
			(*value).u = (*value).u * fScaleFactor;
		}
		
		
	done_heights:
		
		// dispose of GetTideHeight allocated handles
		CleanUpCompHeights(&answers);
		return err;
	}
	
	else if (this->fStationType == 'P')
	{	
		// get the heights
		COMPHEIGHTS answers;
		memset(&answers,0,sizeof(answers));
		err = GetTideHeight(&beginDate,&endDate,
							&fConstituent,	
							YHdl,
							fHeightOffset,
							&answers,
							//**minmaxvalhdl, // not used
							//**minmaxtimehdl, // not used
							//nminmax, // not used
							//*cntrlvars, // not used
							daylightSavings);
		
		//model->NewDirtNotification(DIRTY_LIST);// what we display in the list is invalid
		
		if (!err)
		{
#ifndef pyGNOME
			model->NewDirtNotification(DIRTY_LIST);// what we display in the list is invalid
#endif
			long i,num10MinValues = answers.nPts,numCopied = 0;
			if(num10MinValues > 0 && answers.timeHdl && answers.heightHdl)
			{
				// code goes here, convert the heights into speeds
				TimeValuePairH tvals = (TimeValuePairH)_NewHandle(num10MinValues*sizeof(TimeValuePair));
				if(!tvals) 
				{TechError("TShioTimeValue::GetTimeValue()", "_NewHandle()", 0); err = memFullErr; goto done_heights2;}
				else
				{
					// first copy non-flagged values, then do the derivative in a second loop
					// note this data is no longer used
					//double **heightHdl = (DOUBLEH)_NewHandle(num10MinValues*sizeof(double));
					TimeValuePair tvPair;
					//double deriv;
					for(i = 0; i < num10MinValues; i++)
					{
						if(INDEXH(answers.timeHdl,i).flag == outOfSequenceFlag) continue;// skip this value, code goes here
						if(INDEXH(answers.timeHdl,i).flag == 1) continue;// skip this value, 1 is don't plot flag - junk at beginning or end of data
						// note:timeHdl values are in hrs from start
						tvPair.time = beginSeconds + (long)(INDEXH(answers.timeHdl,i).val*3600); 
						tvPair.value.u = 3048*INDEXH(answers.heightHdl,i)/1200.; // convert to m/s
						tvPair.value.v = 0; // not used
						INDEXH(tvals,numCopied) = tvPair;
						//INDEXH(heightHdl,numCopied) = INDEXH(answers.heightHdl,i);
						numCopied++;
					}
					_SetHandleSize((Handle)tvals, numCopied*sizeof(TimeValuePair));
					this->SetTimeValueHandle(tvals);
					
				}
				////// JLM  , save the highs and lows for displaying on the left hand side
				{
					short	numHighLows = answers.numHighLows;			// Number of high and low tide occurrences.								
					double **HighLowHeightsHdl = answers.HighLowHeightsHdl;	// double feet
					EXTFLAG **HighLowTimesHdl = answers.HighLowTimesHdl;		// double hours, flag=0 means plot
					short			**HighLowHdl = answers.HighLowHdl;			// 0 -> Low Tide.
					// 1 -> High Tide.
					short numToShowUser;
					short i;
					double HighLowHeight;
					EXTFLAG HighLowTime;
					short HighLow;
					
					/////////////////////////////////////////////////
					
					// count the number of values we wish to show to the user
					// (we show the user if the plot flag is set)
					numToShowUser = 0;
					if(HighLowHeightsHdl && HighLowTimesHdl && HighLowHdl)
					{
						for(i = 0; i < numHighLows; i++)
						{
							HighLowTime = INDEXH(HighLowTimesHdl,i);
							if(HighLowTime.flag == 0)
								numToShowUser++;
						}
					}
					
					// now allocate a handle of this size to hold the values for the user
					
					if(fHighLowDataHdl) 
					{
						DisposeHandle((Handle)fHighLowDataHdl); 
						fHighLowDataHdl = 0;
					}
					if(numToShowUser > 0)
					{
						short j;
						fHighLowDataHdl = (HighLowDataH)_NewHandleClear(sizeof(HighLowData)*numToShowUser);
						if(!fHighLowDataHdl) {TechError("TShioTimeValue::GetTimeValue()", "_NewHandleClear()", 0); err = memFullErr; if(tvals)DisposeHandle((Handle)tvals); goto done_heights2;}
						for(i = 0, j=0; i < numHighLows; i++)
						{
							HighLowTime = INDEXH(HighLowTimesHdl,i);
							HighLowHeight = INDEXH(HighLowHeightsHdl,i);
							HighLow = INDEXH(HighLowHdl,i);
							
							if(HighLowTime.flag == 0)
							{
								HighLowData highLowData;
								highLowData.time = beginSeconds + (long) (HighLowTime.val*3600); // value in seconds
								highLowData.height = HighLowHeight; // value in feet
								highLowData.type = HighLow; // 0 -> Low Tide.
								// 1 -> High Tide.
								INDEXH(fHighLowDataHdl,j++) = highLowData;
							}
						}
					}
					
				}
				/////////////////////////////////////////////////
			}
		}
		
		/////////////////////////////////////////////////
		// Find derivative
		if(!err)
		{
			/////////////////////////////////////////////////
			// ask for a scale factor if not known from wizard
			/*fScaleFactor = 1;	// will want a scale factor, but not related to derivative
			 (*value).u = (*value).u * fScaleFactor;*/
			/////////////////////////////////////////////////
			// ask for a scale factor if not known from wizard
			//sprintf(msg,lfFix("The largest calculated derivative was %.4lf"),largestDeriv);
			//strcat(msg, ".  Enter scale factor for heights coefficients file : ");
			char msg[256];
			double scaleFactor;
#ifndef pyGNOME
			strcpy(msg, "Enter scale factor for progressive wave coefficients file : ");
			if (fScaleFactor==0)
			{
				err = GetScaleFactorFromUser(msg,&scaleFactor);
				if (err) goto done_heights2;
				fScaleFactor = scaleFactor;
			}
#endif
			(*value).u = (*value).u * fScaleFactor;
		}
		
		
	done_heights2:
		
		// dispose of GetTideHeight allocated handles
		CleanUpCompHeights(&answers);
		return err;
	}
	
	return TOSSMTimeValue::GetTimeValue(forTime,value);
}

double ShioTimeValue_c::GetDeriv (Seconds t1, double val1, Seconds t2, double val2, Seconds theTime)
{
	double dt = float (t2 - t1) / 3600.;
	if( dt<0.000000001){
		return val2;
	}
	double x = (theTime - t1) / (3600. * dt);
	double deriv = 6. * x * (val1 - val2) * (x - 1.) / dt;
	return (3048./3600.) * deriv;	// convert from ft/hr to m/s, added 10^4 fudge factor so scale is O(1)
}

OSErr ShioTimeValue_c::GetConvertedHeightValue(Seconds forTime, VelocityRec *value)
{
	long i;
	OSErr err = 0;
	HighLowData startHighLowData,endHighLowData;
	for( i=0 ; i<this->GetNumHighLowValues()-1; i++) 
	{
		startHighLowData = INDEXH(fHighLowDataHdl, i);
		endHighLowData = INDEXH(fHighLowDataHdl, i+1);
		if (forTime == startHighLowData.time || forTime == this->GetNumHighLowValues()-1)
		{
			(*value).u = 0.;	// derivative is zero at the highs and lows
			(*value).v = 0.;
			return noErr;
		}
		if (forTime>startHighLowData.time && forTime<endHighLowData.time)
		{
			(*value).u = GetDeriv(startHighLowData.time, startHighLowData.height, 
								  endHighLowData.time, endHighLowData.height, forTime) * fScaleFactor;
			(*value).v = 0.;
			return noErr;
		}
	}
	return -1; // point not found
}

OSErr ShioTimeValue_c::GetProgressiveWaveValue(Seconds forTime, VelocityRec *value)
{
	OSErr err = 0;
	(*value).u = 0;
	(*value).v = 0;
	if (err = TOSSMTimeValue::GetTimeValue(forTime,value)) return err;
	
	(*value).u = (*value).u * fScaleFactor;	// derivative is zero at the highs and lows
	(*value).v = (*value).v * fScaleFactor;
	
	return err;
}

WorldPoint ShioTimeValue_c::GetRefWorldPoint (void)
{
	WorldPoint wp;
	wp.pLat = fLatitude * 1000000;
	wp.pLong = fLongitude * 1000000;
	return wp;
}

/////////////////////////////////////////////////
OSErr ShioTimeValue_c::GetLocationInTideCycle(short *ebbFloodType, float *fraction)
{
	
	Seconds time = model->GetModelTime(), ebbFloodTime;	
	EbbFloodData ebbFloodData1, ebbFloodData2;
	long i, numValues;
	short type;
	float factor;
	OSErr err = 0;
	
	*ebbFloodType = -1;
	*fraction = 0;
	//////////////////////
	if (this->fStationType == 'C')
	{	
		numValues = this->GetNumEbbFloodValues();
		for (i=0; i<numValues-1; i++)
		{
			ebbFloodData1 = INDEXH(fEbbFloodDataHdl, i);
			ebbFloodData2 = INDEXH(fEbbFloodDataHdl, i+1);
			if (ebbFloodData1.time <= time && ebbFloodData2.time > time)
			{
				*ebbFloodType = ebbFloodData1.type;
				*fraction = (float)(time - ebbFloodData1.time) / (float)(ebbFloodData2.time - ebbFloodData1.time);
				return 0;
			}
			if (i==0 && ebbFloodData1.time > time)
			{
				if (ebbFloodData1.type>0) *ebbFloodType = ebbFloodData1.type - 1;
				else *ebbFloodType = 3;
				*fraction = (float)(ebbFloodData1.time - time)/ (float)(ebbFloodData2.time - ebbFloodData1.time);	// a fudge for now
				if (*fraction>1) *fraction=1;
				return 0;
			}
		}
		if (time==ebbFloodData2.time)
		{
			*ebbFloodType = ebbFloodData2.type;
			*fraction = 0;
			return 0;
		}
		printError("Ebb Flood data could not be determined");
		return -1;
	}
	/*else 
	 {
	 printNote("Shio height files aren't implemented for tidal cycle current mover");
	 return -1;
	 }*/
	/////////
	else if (this->fStationType == 'H')
	{
		// this needs work
		Seconds derivTime,derivTime2;
		short type1,type2;
		numValues = 2*(this->GetNumHighLowValues())-1;
		for (i=0; i<numValues; i++) // show only max/mins, converted from high/lows
		{
			HighLowData startHighLowData,endHighLowData,nextHighLowData;
			double maxMinDeriv;
			Seconds midTime,midTime2;
			long index = floor(i/2.);
			
			startHighLowData = INDEXH(fHighLowDataHdl, index);
			endHighLowData = INDEXH(fHighLowDataHdl, index+1);
			
			midTime = (endHighLowData.time - startHighLowData.time)/2 + startHighLowData.time;
			midTime2 = (endHighLowData.time - startHighLowData.time)/2 + endHighLowData.time;
			
			switch(startHighLowData.type)
			{
				case	LowTide:
					if (fmod(i,2.) == 0)	
					{
						derivTime = startHighLowData.time;
						type1 = MinBeforeFlood;
					}
					else	
					{
						derivTime = midTime;
						type1 = MaxFlood;
					}
					break;
				case	HighTide:
					if (fmod(i,2.) == 0)	
					{
						derivTime = startHighLowData.time;
						type1 = MinBeforeEbb;
					}
					else 
					{
						derivTime = midTime;
						type1 = MaxEbb;
					}
					break;
			}
			switch(endHighLowData.type)
			{
				case	LowTide:
					if (fmod(i,2.) == 0)	
					{
						derivTime2 = endHighLowData.time;
						type2 = MinBeforeFlood;
					}
					else	
					{
						derivTime2 = midTime2;
						type2 = MaxFlood;
					}
					break;
				case	HighTide:
					if (fmod(i,2.) == 0)	
					{
						derivTime2 = endHighLowData.time;
						type2 = MinBeforeEbb;
					}
					else 
					{
						derivTime2 = midTime2;
						type2 = MaxEbb;
					}
					break;
			}
			//maxMinDeriv = GetDeriv(startHighLowData.time, startHighLowData.height,
			//endHighLowData.time, endHighLowData.height, derivTime) * fScaleFactor / KNOTSTOMETERSPERSEC;

			//StringWithoutTrailingZeros(valStr,maxMinDeriv,1);
			//SecondsToDate(derivTime, &time);
			if (derivTime <= time && derivTime2 > time)
			{
				*ebbFloodType = type1;
				*fraction = (float)(time - derivTime) / (float)(derivTime2 - derivTime);
				return 0;
			}
			if (i==0 && derivTime > time)
			{
				if (type1>0) *ebbFloodType = type1 - 1;
				else *ebbFloodType = 3;
				*fraction = (float)(derivTime - time)/ (float)(derivTime2 - derivTime);	// a fudge for now
				if (*fraction>1) *fraction=1;
				return 0;
			}
		}
		if (time==derivTime2)
		{
			*ebbFloodType = type2;
			*fraction = 0;
			return 0;
		}
		printError("Ebb Flood data could not be determined");
		return -1;
	}

	return 0;
}



OSErr ShioTimeValue_c::GetTimeChange(long a, long b, Seconds *dt)
{	// having this this function is inherited but meaningless
	this->ProgrammerError("GetTimeChange");
	*dt = 0;
	return -1;
}

OSErr ShioTimeValue_c::GetInterpolatedComponent(Seconds forTime, double *value, short index)
{	// having this function is inherited but meaningless
	this->ProgrammerError("GetInterpolatedComponent");
	*value = 0;
	return -1;
}

