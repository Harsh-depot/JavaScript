const myArr = [1, 2, 3, 4, 5];
const myHeros = ["Spiderman", "Ironman", "Hulk", "Thor", "Captain America"];

// Accessing array elements
// console.log(myArr[0]); // Output: 1
// console.log(myHeros[2]); // Output: Hulk

const myArr2 = new Array(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10); // Creates an array with 10 elements
// console.log(myArr[2]);

// myArr.push(6); // Adds 6 to the end of the array
// myArr.push(7); // Adds 7 to the end of the array
// myArr.pop(); // Removes the last element from the array

// myArr.unshift(9); // Adds 9 to the beginning of the array
// myArr.shift(); // Removes the first element from the array

// console.log(myArr.includes(3)); // Output: true
// console.log(myArr.includes(9)); // Output: false
// console.log(myArr.indexOf(3)); // Output: 2

const newArr = myArr.join();

// console.log(myArr);
// console.log(newArr);
// console.log(typeof newArr); // Output: string

// slice, splice

// console.log("A", myArr);

const myn1 = myArr.slice(1,3); // Creates a new array with elements from index 1 to 3 (not including index 3)

// console.log(myn1);
// console.log("B", myArr);

const myn2 = myArr.splice(1,3); // Removes 3 elements from index 1 and returns them as a new array

// console.log(myn2);
// console.log("C", myArr);

