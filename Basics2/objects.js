// singleton

// object literal

const mySym = Symbol("key1")

const Jsusers = {
    name: "Harsh",
    "full name": "Harshvardhan Raj",
    [mySym]: "mykey1",
    age: 20,
    location: "India",
    email: "harsh@example.com",
    isLoggedIn: false,
    lastLoginDays: ["Monday", "Tuesday", "Wednesday"],
}

// console.log(Jsusers.name); // it's not a good practice to use dot notation when the key is not a valid identifier or is a variable. In such cases, bracket notation should be used.
// console.log(Jsusers.email);
// console.log(Jsusers["email"]) // bracket notation is used when the key is not a valid identifier or is a variable. In such cases, bracket notation should be used.
// console.log(Jsusers["full name"]);
// console.log(Jsusers.mySym); // here the output ddata type is a string, which it isn't supposed to...
// console.log(Jsusers[mySym]);

Jsusers.email = "harsh@chatgpt.com" 
//Object.freeze(Jsusers)
Jsusers.email = "harsh@microsoft.com"
// console.log(Jsusers);

Jsusers.greeting = function(){
    console.log("Hello JS user");
}

Jsusers.greetingTwo = function(){
    console.log(`Hello Js user, ${this.name}`);
}

// when run but with the freeze statement...
//console.log(Jsusers.greeting); // the output is undefined.
// console.log(Jsusers.greeting()); //output = Jsusers.greeting is not a function.

// when freeze statement is removed...
//console.log(Jsusers.greeting); // output = [Function (anonymous)]
console.log(Jsusers.greeting()); // output = Hello JS user,undefined

console.log(Jsusers.greetingTwo());