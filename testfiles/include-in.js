
var foo = function() {
  alert('starting...');

  //@include ../testfiles/include-data.js

  //@include include-data.js

  alert('This.');
  alert('That.');
};

//@include ifdef-hash-in.js
