'''
    VTT transcript parser
    
    Converts series of VTT-format caption files into a single SRT-format
    Good for combining Zoom-generated captions for separate videos

    cameron f abrams -- cfa22@drexel.edu
'''

import sys

class Timestamp:
    def __init__(self,istr,style='SRT'):
        if style=='SRT':
            self.s_ms_sep=','
        else:
            self.s_ms_sep='.'
        if istr[0]=='-':
            self.sign=-1
            self.h=int(istr[1:3])
            self.m=int(istr[4:6])
            self.s=int(istr[7:9])
            self.ms=int(istr[10:13])
        elif istr[0].isdigit():
            self.sign=1
            self.h=int(istr[0:2])
            self.m=int(istr[3:5])
            self.s=int(istr[6:8])
            self.ms=int(istr[9:12])
        else:
            print('Error: malformed timestamp string: {}'.format(istr))
            exit()
        self.AMS=self.ms+1000*(self.s+60*(self.m+60*self.h))
        if self.sign==-1:
            self.AMS*=-1
    def decomp(self):
        WMS=abs(self.AMS)
        self.ms=WMS%1000
        WSEC=(WMS-self.ms)//1000
        self.s=WSEC%60
        WMIN=(WSEC-self.s)//60
        self.m=WMIN%60
        self.h=(WMIN-self.m)//60
        if self.AMS<0:
           self.sign=-1
        else:
           self.sign=1
    def add(self,b):
        self.AMS+=b.AMS
        self.decomp()
        return self
    def cpy(self):
        newint=Timestamp(str(self))
        newint.s_ms_sep=self.s_ms_sep
        return newint
    def __str__(self,style='SRT'):
        return '{}{:02d}:{:02d}:{:02d}{:s}{:03d}'.format('' if self.sign==1 else '-',self.h,self.m,self.s,self.s_ms_sep,self.ms)

_zero_stamp_=Timestamp('00:00:00,000')

class Interval:
    def __init__(self,beg,end,pad=_zero_stamp_):
        self.beg=beg.add(pad)
        self.end=end.add(pad)
    def __str__(self):
        return str(self.beg)+' --> '+str(self.end)

class Caption:
    def __init__(self,index,interval,caption):
        self.index=index
        self.interval=interval
        self.caption=caption
    def __str__(self):
        retstr='{}\n'.format(self.index)+str(self.interval)+'\n'+self.caption+'\n'
        retstr=retstr.replace('Cameron Abrams: ','')
        return retstr
        #return str(self.interval)+'\n'+self.caption+'\n'
 
def read_captions(fn,time_shifts=[],instyle='VTT'):
    Captions=[]
    lines=[]
    cuts=[]
    outstyle='SRT'
    i=0
    for f in fn:
        with open(f,'r') as g:
            for l in g:
                lines.append(l)
                i+=1
            cuts.append(i)
    cut=0
    if len(time_shifts)>0:
        pad=time_shifts[0]
    else:
        pad=Timestamp('00:00:00,000',outstyle)
    last_index=0
    i=0
    while i<len(lines):
        l=lines[i]
        ll=l.split()
        atCap=False
        if instyle=='VTT':
            if len(ll)==1 and ll[0][0].isdigit():
                index=int(ll[0])+last_index
                #print(index)
                i+=1
                atCap=True
                ll=lines[i].split()
        elif instyle=='SRT':
           # print(ll)
            if len(ll)==3 and ll[1]=='-->':
                index=1+last_index
                atCap=True
        if atCap:
            Captions.append(Caption(index,Interval(Timestamp(ll[0],outstyle),Timestamp(ll[2],outstyle),pad),lines[i+1]))
        i+=1
        if i==cuts[cut] and cut<len(cuts)-1:
            pad=Captions[-1].interval.end.cpy() # for linking if timer starts over in next file
            pad.add(time_shifts[cut+1])
            last_index=index
            cut+=1
    return Captions


if __name__=='__main__':
    outstyle='SRT'
    instyle='VTT'
    i=1
    fn=[]
    ts=[]
    while i<len(sys.argv):
        if sys.argv[i]=='-ts':
            i+=1
            tss=sys.argv[i].split()
            #print('tss',tss)
            for t in tss:
                ts.append(Timestamp(t))
        elif sys.argv[i]=='-vtt': # begin file list
            instyle='VTT'
            i+=1
            while i<len(sys.argv) and sys.argv[i][0]!='-':
                fn.append(sys.argv[i])
                i+=1
            if i<len(sys.argv):
                i-=1
        elif sys.argv[i]=='-srt': # begin file list
            instyle='SRT'
            i+=1
            while i<len(sys.argv) and sys.argv[i][0]!='-':
                fn.append(sys.argv[i])
                i+=1
            if i<len(sys.argv):
                i-=1
        i+=1
    if len(fn)==0:
        exit()
    Captions=read_captions(fn,time_shifts=ts,instyle=instyle)
    for c in Captions:
        print(c,end='')
