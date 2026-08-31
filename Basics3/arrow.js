const user = {
    username: "harsh",
    price: 999,
    welcomeMessage: function() {
        console.log(`${this.username} , welcome to website`);
        // console.log(this); // tells everything about the current context/values.
        
    }
}

// user.welcomeMessage()
// user.username = "harry"
// user.welcomeMessage()

// console.log(this); // gives empty {}, as there is no current values or context. 

// function chai() {
//     let  username = "harsh"
//     console.log(this.username); // output = undefined
// }

// chai() // we can't use 'this' in functiions.

// const chai = function () {
//     let  username = "harsh"
//     console.log(this.username);
// }

// chai()  // output = undefined.


// const chai = () => {
//     let  username = "harsh"
//     console.log(this.username);
// }

// chai() // output = undefined.

// const addTwo = (num1, num2) => {
//     return num1 + num2
// }
// console.log(addTwo(3,4));

const addTwo = (num1, num2) => (num1 + num2)
console.log(addTwo(3,4));
// when using {} we have to write return but in case of (), we don't need return statement.
