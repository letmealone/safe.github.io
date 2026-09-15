render();resetNavigation();
const entryParams=new URLSearchParams(location.search);
if(entryParams.has('tour')&&/^\d+$/.test(entryParams.get('tour')))showTourStep(Number(entryParams.get('tour')));
else if(entryParams.has('step')&&/^\d+$/.test(entryParams.get('step')))jumpTo(Number(entryParams.get('step')));
