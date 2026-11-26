# plus1_check_lipt.R - check for added constants in offsets and log transforms (log1p variants).
# Part of the analysis code for lifestyle-treated-dyslipidemia-korea (v1.0.1, MIT license). See README.md (Pipeline) for how to run.
suppressPackageStartupMessages({library(INLA);library(sf);library(jsonlite)})
inla.setOption(num.threads="1:1")
TAG<-"LIPT";VER<-"std3";OUTD<-file.path("..","04_분석",TAG);RES<-file.path(OUTD,paste0("results_",VER),"plus1_check");dir.create(RES,showWarnings=FALSE,recursive=TRUE)
S<-fromJSON(file.path(OUTD,sprintf("config_%s_%s.json",TAG,VER)),simplifyVector=TRUE)
DD<-read.csv(file.path(OUTD,sprintf("panel_%s_%s.csv",TAG,VER)),fileEncoding="UTF-8-BOM",stringsAsFactors=FALSE);DD$fbd_region<-enc2utf8(DD$fbd_region)
G<-st_read(Sys.getenv("ST_SHP"),quiet=TRUE);G$region<-enc2utf8(G$region);g<-inla.read.graph(Sys.getenv("ST_GRAPH"));stopifnot(g$n==nrow(G))
DD$area<-match(DD$fbd_region,G$region);DD$time<-DD$year-min(DD$year)+1;DD$yiid<-DD$time
FORCED<-S$forced;HYP<-as.character(S$sets_after_vif$S1_narrative_full);MAIN<-unique(c(HYP,FORCED));V<-"im_specialists_per_100k"
cat(sprintf("offset check: E min %.3f, E==E_std(+1 없음) 81 E=data[['E']]\n",min(DD$E)))
x<-expm1(DD$im_specialists_per_100k_raw);stopifnot(max(abs(log1p(x)-DD$im_specialists_per_100k_raw))<1e-12)
cat(sprintf("im_specialists per100k: zero cells %d, positive min %.4f\n",sum(x==0),min(x[x>0])))
fillz<-function(v){d<-data.frame(k=DD$key,y=DD$year,v=v);o<-order(d$k,d$y);d<-d[o,]
  d$v1<-ave(d$v,d$k,FUN=function(s){if(sum(!is.na(s))>=2)approx(seq_along(s),s,xout=seq_along(s),rule=1)$y else s})
  d$v2<-ifelse(is.na(d$v1),ave(d$v1,d$k,FUN=function(s)mean(s,na.rm=TRUE)),d$v1);d$v2[is.nan(d$v2)]<-NA
  d$v3<-ifelse(is.na(d$v2),ave(d$v2,d$y,FUN=function(s)mean(s,na.rm=TRUE)),d$v2);r<-numeric(nrow(d));r[o]<-d$v3;(r-mean(r))/sqrt(mean((r-mean(r))^2))}
c0<-min(x[x>0])/2
sus<-(grepl("군위",DD$fbd_region)&DD$year==2023)|(grepl("영양",DD$fbd_region)&DD$year==2019);stopifnot(sum(sus)==2,all(x[sus]==0))
VAR<-list(orig_rep1=DD[[V]],orig_rep2=DD[[V]],gunwi_yeongyang_zero_interp=fillz(ifelse(sus,NA,log1p(x))),halfmin=fillz(log(x+c0)),zeroNA_fill=fillz(ifelse(x>0,log(x),NA)),linear=fillz(x))
stopifnot(max(abs(fillz(log1p(x))-DD[[V]]))<1e-9)
pc<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)),phi=list(prior="pc",param=c(0.5,2/3)));pcp<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)))
fit<-function(d){f<-as.formula(paste("cases ~ 1 +",paste(sprintf("`%s`",MAIN),collapse="+"),"+ f(area,model='bym2',graph=g,scale.model=TRUE,constr=TRUE,hyper=pc) + f(time,model='rw1',scale.model=TRUE,hyper=pcp) + f(yiid,model='iid',hyper=pcp)"))
  inla(f,family="nbinomial",data=d,E=d$E,control.fixed=list(mean=0,prec=4,mean.intercept=0,prec.intercept=0.001),control.compute=list(waic=TRUE,dic=TRUE),control.inla=list(control.vb=list(emergency=50)))}
FX<-NULL;FS<-NULL
for(nm in names(VAR)){d<-DD;d[[V]]<-VAR[[nm]];t0<-Sys.time();m<-fit(d);fx<-m$summary.fixed[MAIN,]
  FX<-rbind(FX,data.frame(variant=nm,cov=MAIN,IRR=exp(fx$mean),lo=exp(fx$`0.025quant`),hi=exp(fx$`0.975quant`),cred=(fx$`0.025quant`>0|fx$`0.975quant`<0)))
  FS<-rbind(FS,data.frame(variant=nm,WAIC=m$waic$waic,DIC=m$dic$dic,minutes=as.numeric(difftime(Sys.time(),t0,units="mins"))))
  cat(sprintf("%s done WAIC %.1f IRR(%s)=%.4f (%.4f-%.4f)\n",nm,m$waic$waic,V,exp(fx[V,"mean"]),exp(fx[V,"0.025quant"]),exp(fx[V,"0.975quant"])))}
write.csv(FX,file.path(RES,"plus1_fixed_all.csv"),row.names=FALSE);write.csv(FS,file.path(RES,"plus1_fitstats.csv"),row.names=FALSE)
cat("ALL DONE plus1\n")
