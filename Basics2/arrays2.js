const marvel_heroes = ['Iron Man', 'Captain America', 'Thor', 'Hulk'];
const dc_heroes = ['Batman', 'Superman', 'Wonder Woman', 'Flash'];

// marvel_heroes.push(dc_heroes); // Adds the dc_heroes array as a single element to the end of the marvel_heroes array
// console.log(marvel_heroes); // Output: ['Iron Man', 'Captain America', 'Thor', 'Hulk', ['Batman', 'Superman', 'Wonder Woman', 'Flash']]

// const allHeroes = marvel_heroes.concat(dc_heroes); // Creates a new array by concatenating marvel_heroes and dc_heroes, but does not modify marvel_heroes
// console.log(allHeroes); // Output: ['Iron Man', 'Captain America', 'Thor', 'Hulk', 'Batman', 'Superman', 'Wonder Woman', 'Flash']

// const allnewHeroes = [...marvel_heroes, ...dc_heroes]; // Creates a new array by spreading the elements of marvel_heroes and dc_heroes into a new array
// console.log(allnewHeroes); // Output: ['Iron Man', 'Captain America', 'Thor', 'Hulk', 'Batman', 'Superman', 'Wonder Woman', 'Flash']

const another_array = [1, 2, 3, [4, 5, 6], 7, [8, 9, 11, [12, 13, 14]]];
const real_another_array = another_array.flat(3);
// console.log(real_another_array); // Output: [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14]

// console.log(Array.isArray("Harsh"))
// console.log(Array.from("Harsh"))
// console.log(Array.from({name: "Harsh"})) // Output: [undefined]

let score1 = 100
let score2 = 200
let score3 = 300
console.log(Array.of(score1, score2, score3)) // Output: [100, 200, 300]