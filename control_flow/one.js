// if


// const isUserLoogedIn = true
// const temparature = 41
// if ( temparature < 50) {
//     console.log("temparature is less than 50!!!");
// } else {
//     console.log("temparature is greater than 50!!!");
// }
// console.log("Executed...");

// here the local scope is done first then global scope is done... point to note is that the global scope will be done no matter what the local output is...

// < (for greater than) , > (for less than) , <= (for less than or equal to) , >= (for greater than or equal to) , == (for equal to) , != (for not equal to) , === (for strict equal to) , !== (for strict not equal to) 


// const score = 200
// if (score > 100){
//     const power = "fly"
//     console.log(`user power is ${power}`);
// }

// code is for the global and local scope... it tells that the variables used in a local scope is not available globally... ofc there is an execption of using "var" but again... this just makes everthing messy.

const balance = 1000

// if (balance > 500) console.log("test"),
// console.log("test2");

// this is also a way to write the syntax but it isnot highly appriciated...

// if (balance < 500) {
//     console.log("less than 500");
// } else if (balance < 750) {
//     console.log("less than 750");
// } else if (balance < 900) {
//     console.log("less than 900");
// } else {
//     console.log("less than 1200");
// }

// nested if else


const userLoggedIn = true
const debitCard = true
const loggedInFromGoogle = false
const loggedInFromEmail = true

if (userLoggedIn && debitCard) {
    console.log("Allow to buy courses");
}

if (loggedInFromGoogle || loggedInFromEmail) {
    console.log("User logged in...");
}
