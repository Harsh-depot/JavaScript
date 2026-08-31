// Local scope

if (true) {
    let a = 10
    const b = 20
    var c = 30
}

// console.log(a);  // output = a is not defined
// console.log(b);  // output = b is not defined
// console.log(c);  // output = 30 (which should not be possible as a,b,c all are in the conditional statement. but the c gets out of the statement and is given as an output)


// Global scope
let a = 300

if (true) {
    let a = 10
    const b = 20
    // var c = 30
    // console.log("INNER: ", a);
    function addnum() {
        
    }
}


// console.log(a);

function one() {
    const username = "harsh"

    function two() {
        const website = "github"
        console.log(username);
    }
    // console.log(website);

    two()
    
}

one()

if (true) {
    const username = "harsh"
    if (username === "harsh") {
        const website = " github"
        console.log(username + website);
        
    }
    // console.log(website); // output = website is not defined (local can acces the values of global scope but global can't access the values of local scopes, this also happens in the nested loops... chaid have the access of parents values but parents ccan't access the value inside of the child loop).
}

// console.log(username);  // output = username is not defined (username is inside the local scope so it can't  be accessed globally)


// +++++++++++++++++++++ intersting ++++++++++++++++

function addone(num) {
    return num + 1
}
addone(5)



const  addTwo =  function(num) {
    return num + 2
}

addTwo(5)


// console.log(addTwo(5)); // output = Cannot access 'addTwo' before initialization. Because, In this method we have hold the fuction in a variable.
// const  addTwo =  function(num) {
//     return num + 2
// }

