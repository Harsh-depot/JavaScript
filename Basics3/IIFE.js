// Immediately Invoked Function Expressions (IIFE)

(function chai() {
    // named IIFE
    console.log(`DB CONNECTED`);
})();
// WE NEED TO ADD ; TO END THE FUNTION WHEN CALLING IMMEDIATELY, THIS WAS NOT THE CASE IN DIRECT CALL.

((name) => {
    // simple iife
        console.log(`DB2 CONNECTED for ${name}`);
        
    }
)('harsh');