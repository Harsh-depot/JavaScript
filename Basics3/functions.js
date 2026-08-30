function sayMyName (){
    console.log("H");
    console.log("A");
    console.log("R");
    console.log("S");
    console.log("H");
}

// sayMyName()

// function addTwoNumbers(number1, number2){
//     console.log(number1 + number2);
// }

function addTwoNumbers(number1, number2){
    // let result = number1 + number2
    // return result
    return number1 + number2
}


// addTwoNumbers(3,4) // output = 7
// addTwoNumbers(3,"4") // output = 34
// addTwoNumbers(3,null) // output = 3
// addTwoNumbers(3,a) // output = a is not defined
// addTwoNumbers() // output = NaN

const result = addTwoNumbers(3,5)
// console.log("Result: ", result);

function loginUserMessege(username){
    if(username === undefined){
        console.log("Please enter a username");
        return
    }
    return `${username} just logged in`
}
// we can use ! for signifing not value... i.e. username === undefined can be written as !username.
// console.log(loginUserMessege("harsh")); // output = harsh just logged in
// console.log(loginUserMessege()); // output = undefined just logged in

// function calculateCartPrice(...num1){
//     return num1
// }


function calculateCartPrice(val1, val2, ...num1){
    return num1
}

// console.log(calculateCartPrice(200, 400, 500, 2000))

const user = {
    username: "hitesh",
    price: 199
}

function handleObject(anyobject){
    console.log(`Username is ${anyobject.username} and price is ${anyobject.price}`);
}

handleObject(user)
handleObject({
    username: "sam",
    price: 399
})

const myNewArray = [200, 400, 100, 600]

function returnSecondValue(getArray){
    return getArray[1]
}

console.log(returnSecondValue(myNewArray));
console.log(returnSecondValue([200, 400, 500, 1000]));