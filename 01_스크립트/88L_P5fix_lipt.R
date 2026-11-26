# 88L_P5fix_lipt.R - post hoc specialists per area (count divided by area).
# Part of the analysis code for lifestyle-treated-dyslipidemia-korea (v1.0.1, MIT license). See README.md (Pipeline) for how to run.
suppressPackageStartupMessages({library(INLA);library(sf);library(jsonlite)})
TAG<-Sys.getenv("TAG","LIPT");VER<-Sys.getenv("ST_VER","std3");inla.setOption(num.threads="1:1")
OUTD<-file.path("..","04_분석",TAG);RES<-file.path(OUTD,paste0("results_",VER))
SHP<-Sys.getenv("ST_SHP",file.path(normalizePath(file.path(dirname(sub("--file=","",grep("--file=",commandArgs(),value=TRUE))),"..")),"data","boundary","final.shp"))
S<-fromJSON(file.path(OUTD,sprintf("config_%s_%s.json",TAG,VER)),simplifyVector=TRUE)
DD<-read.csv(file.path(OUTD,sprintf("panel_%s_%s.csv",TAG,VER)),fileEncoding="UTF-8-BOM",stringsAsFactors=FALSE);DD$fbd_region<-enc2utf8(DD$fbd_region)
G<-st_read(SHP,quiet=TRUE);G$region<-enc2utf8(G$region);g<-inla.read.graph(Sys.getenv("ST_GRAPH"));stopifnot(g$n==nrow(G))
DD$area<-match(DD$fbd_region,G$region);DD$time<-DD$year-min(DD$year)+1;DD$yiid<-DD$time
FORCED<-S$forced;HYP<-as.character(S$sets_after_vif$S1_narrative_full)
pc<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)),phi=list(prior="pc",param=c(0.5,2/3)));pcp<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)))
REV<-c("im_specialists_per_100k");EXTRA<-character(0)
z<-function(x)(x-mean(x))/sd(x)
DD$spec_per_km2_log<-z(log1p(expm1(DD$im_specialists_per_100k_raw)*DD$population/1e5/(DD$area_m2/1e6)))
DD$spec_per_km2_log_altdef<-z(log1p(DD$im_specialists_per_100k_raw*DD$population/1e5/(DD$area_m2/1e6)))
cat(sprintf("cor(corrected, original definition) = %.4f\n",cor(DD$spec_per_km2_log,DD$spec_per_km2_log_altdef)))
for(v in REV){m<-ave(DD[[v]],DD$fbd_region);DD[[paste0(v,"__B")]]<-(m-mean(m))/sd(m);w<-DD[[v]]-m;DD[[paste0(v,"__W")]]<-w/sd(w)}
fit<-function(vars){f<-as.formula(paste("cases ~ 1 +",paste(sprintf("`%s`",vars),collapse="+"),"+ f(area,model='bym2',graph=g,scale.model=TRUE,constr=TRUE,hyper=pc) + f(time,model='rw1',scale.model=TRUE,hyper=pcp) + f(yiid,model='iid',hyper=pcp)"))
  inla(f,family="nbinomial",data=DD,E=DD$E,control.fixed=list(mean=0,prec=4,mean.intercept=0,prec.intercept=0.001),control.compute=list(waic=TRUE),control.inla=list(control.vb=list(emergency=50)))}
out<-NULL
add<-function(an,m,vs){fx<-m$summary.fixed;for(v in vs){if(!v%in%rownames(fx))next;r<-fx[v,];out<<-rbind(out,data.frame(analysis=an,cov=v,IRR=round(exp(r$mean),4),lo=round(exp(r$`0.025quant`),4),hi=round(exp(r$`0.975quant`),4),cred=(exp(r$`0.025quant`)>1|exp(r$`0.975quant`)<1),WAIC=round(m$waic$waic,1)))};cat(an,"done\n")}
MAIN<-unique(c(HYP,FORCED));SENS<-intersect(c("ext__unmet_need_rate","ext__dx_htn_share","ext__dx_dm_share"),names(DD))
V<-"im_specialists_per_100k"
add("P5_per_area_fix",fit(c(setdiff(MAIN,V),"spec_per_km2_log")),"spec_per_km2_log")
add("P5b_both_fix",fit(c(MAIN,"spec_per_km2_log")),c(V,"spec_per_km2_log"))
write.csv(out,file.path(RES,"S46c_lipt_posthoc_P5fix.csv"),row.names=FALSE);print(out)
