/*
Project : PyvoA
Date :    april 2020 - november 2025
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pyvoa_org
License: See joint LICENSE file
https://pyvoa.org/

Module : js/rollover_callback.js

About :
-------
*/
var value;
//   if(Math.abs(value)>100000 || Math.abs(value)<0.001)
//       return value.toExponential(2);
//   else
//       return value.toFixed(2);
if(value>10000 || value <0.01)
	value =  Number.parseFloat(value).toExponential(2);
else
	value = Number.parseFloat(value).toFixed(2);
return value.toString();
/*  var s = value;
		  var s0=s;
		  var sp1=s.split(".");
		  var p1=sp1[0].length
		  if (sp1.length>1) {
		    var sp2=s.split("e");
		    var p2=sp2[0].length
		    var p3=p2
		    while(s[p2-1]=="0" && p2>p1) {
			p2=p2-1;
		    }
		    s=s0.substring(0,p2)+s0.substring(p3,s0.length);
		  }
		  if (s.split(".")[0].length==s.length-1) {
		    s=s.substring(0,s.length-1);
		  }
		  return s;
*/
