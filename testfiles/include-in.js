
var foo = function() {
  alert('starting...');

  //@include ../testfiles/include-data.js
  //@end

  //@include include-data.js
  //@end

  alert('This.');
  alert('That.');
};

//@include ifdef-hash-in.js
//@end
