// @__file__ line @__line__

// This next bit closes over a `define`. //@strip
// However, it shouldn't run the define since FOO hasn't been defined yet. //@strip
//#ifndef FOO
// FOO not defined. Correct.
//#define BLAH 1
//#endifndef

//#ifdef BLAH
// Blah PASS
//#else
// Blah FAIL
//#endif

// Now we define FOO and BAR //@strip
//@define FOO 0
//@define BAR 1

var foo = function() {
  // The ABCDE line should be in the output.
  //@if BAR
  alert('ABCDE');
  //@endif

  alert('This line should not be in the output!'); //@strip

  // The RAINDROP line should be in the output.
  //@if (FOO or BAR)
  alert('RAINDROP');
  //@end

  // The CATMAGIC line should be in the output.
  var bar = "CATMAGIC";

  // The BITS line should be in the output.
  //@ifdef (FOO or BAR)
  alert('BITS');
  //@endifdef

  //@if FOO
  alert('Foo is false, so this line should be gone.');
  //@endif
};
