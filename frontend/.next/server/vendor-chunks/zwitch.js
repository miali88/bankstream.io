"use strict";
/*
 * ATTENTION: An "eval-source-map" devtool has been used.
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file with attached SourceMaps in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
exports.id = "vendor-chunks/zwitch";
exports.ids = ["vendor-chunks/zwitch"];
exports.modules = {

/***/ "(rsc)/./node_modules/zwitch/index.js":
/*!**************************************!*\
  !*** ./node_modules/zwitch/index.js ***!
  \**************************************/
/***/ ((__unused_webpack___webpack_module__, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   zwitch: () => (/* binding */ zwitch)\n/* harmony export */ });\n/**\n * @callback Handler\n *   Handle a value, with a certain ID field set to a certain value.\n *   The ID field is passed to `zwitch`, and it’s value is this function’s\n *   place on the `handlers` record.\n * @param {...any} parameters\n *   Arbitrary parameters passed to the zwitch.\n *   The first will be an object with a certain ID field set to a certain value.\n * @returns {any}\n *   Anything!\n */\n\n/**\n * @callback UnknownHandler\n *   Handle values that do have a certain ID field, but it’s set to a value\n *   that is not listed in the `handlers` record.\n * @param {unknown} value\n *   An object with a certain ID field set to an unknown value.\n * @param {...any} rest\n *   Arbitrary parameters passed to the zwitch.\n * @returns {any}\n *   Anything!\n */\n\n/**\n * @callback InvalidHandler\n *   Handle values that do not have a certain ID field.\n * @param {unknown} value\n *   Any unknown value.\n * @param {...any} rest\n *   Arbitrary parameters passed to the zwitch.\n * @returns {void|null|undefined|never}\n *   This should crash or return nothing.\n */\n\n/**\n * @template {InvalidHandler} [Invalid=InvalidHandler]\n * @template {UnknownHandler} [Unknown=UnknownHandler]\n * @template {Record<string, Handler>} [Handlers=Record<string, Handler>]\n * @typedef Options\n *   Configuration (required).\n * @property {Invalid} [invalid]\n *   Handler to use for invalid values.\n * @property {Unknown} [unknown]\n *   Handler to use for unknown values.\n * @property {Handlers} [handlers]\n *   Handlers to use.\n */\n\nconst own = {}.hasOwnProperty\n\n/**\n * Handle values based on a field.\n *\n * @template {InvalidHandler} [Invalid=InvalidHandler]\n * @template {UnknownHandler} [Unknown=UnknownHandler]\n * @template {Record<string, Handler>} [Handlers=Record<string, Handler>]\n * @param {string} key\n *   Field to switch on.\n * @param {Options<Invalid, Unknown, Handlers>} [options]\n *   Configuration (required).\n * @returns {{unknown: Unknown, invalid: Invalid, handlers: Handlers, (...parameters: Parameters<Handlers[keyof Handlers]>): ReturnType<Handlers[keyof Handlers]>, (...parameters: Parameters<Unknown>): ReturnType<Unknown>}}\n */\nfunction zwitch(key, options) {\n  const settings = options || {}\n\n  /**\n   * Handle one value.\n   *\n   * Based on the bound `key`, a respective handler will be called.\n   * If `value` is not an object, or doesn’t have a `key` property, the special\n   * “invalid” handler will be called.\n   * If `value` has an unknown `key`, the special “unknown” handler will be\n   * called.\n   *\n   * All arguments, and the context object, are passed through to the handler,\n   * and it’s result is returned.\n   *\n   * @this {unknown}\n   *   Any context object.\n   * @param {unknown} [value]\n   *   Any value.\n   * @param {...unknown} parameters\n   *   Arbitrary parameters passed to the zwitch.\n   * @property {Handler} invalid\n   *   Handle for values that do not have a certain ID field.\n   * @property {Handler} unknown\n   *   Handle values that do have a certain ID field, but it’s set to a value\n   *   that is not listed in the `handlers` record.\n   * @property {Handlers} handlers\n   *   Record of handlers.\n   * @returns {unknown}\n   *   Anything.\n   */\n  function one(value, ...parameters) {\n    /** @type {Handler|undefined} */\n    let fn = one.invalid\n    const handlers = one.handlers\n\n    if (value && own.call(value, key)) {\n      // @ts-expect-error Indexable.\n      const id = String(value[key])\n      // @ts-expect-error Indexable.\n      fn = own.call(handlers, id) ? handlers[id] : one.unknown\n    }\n\n    if (fn) {\n      return fn.call(this, value, ...parameters)\n    }\n  }\n\n  one.handlers = settings.handlers || {}\n  one.invalid = settings.invalid\n  one.unknown = settings.unknown\n\n  // @ts-expect-error: matches!\n  return one\n}\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiKHJzYykvLi9ub2RlX21vZHVsZXMvendpdGNoL2luZGV4LmpzIiwibWFwcGluZ3MiOiI7Ozs7QUFBQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0EsV0FBVyxRQUFRO0FBQ25CO0FBQ0E7QUFDQSxhQUFhO0FBQ2I7QUFDQTs7QUFFQTtBQUNBO0FBQ0E7QUFDQTtBQUNBLFdBQVcsU0FBUztBQUNwQjtBQUNBLFdBQVcsUUFBUTtBQUNuQjtBQUNBLGFBQWE7QUFDYjtBQUNBOztBQUVBO0FBQ0E7QUFDQTtBQUNBLFdBQVcsU0FBUztBQUNwQjtBQUNBLFdBQVcsUUFBUTtBQUNuQjtBQUNBLGFBQWE7QUFDYjtBQUNBOztBQUVBO0FBQ0EsY0FBYyxnQkFBZ0I7QUFDOUIsY0FBYyxnQkFBZ0I7QUFDOUIsY0FBYyx5QkFBeUI7QUFDdkM7QUFDQTtBQUNBLGNBQWMsU0FBUztBQUN2QjtBQUNBLGNBQWMsU0FBUztBQUN2QjtBQUNBLGNBQWMsVUFBVTtBQUN4QjtBQUNBOztBQUVBLGNBQWM7O0FBRWQ7QUFDQTtBQUNBO0FBQ0EsY0FBYyxnQkFBZ0I7QUFDOUIsY0FBYyxnQkFBZ0I7QUFDOUIsY0FBYyx5QkFBeUI7QUFDdkMsV0FBVyxRQUFRO0FBQ25CO0FBQ0EsV0FBVyxxQ0FBcUM7QUFDaEQ7QUFDQSxjQUFjO0FBQ2Q7QUFDTztBQUNQOztBQUVBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBLFlBQVk7QUFDWjtBQUNBLGFBQWEsU0FBUztBQUN0QjtBQUNBLGFBQWEsWUFBWTtBQUN6QjtBQUNBLGdCQUFnQixTQUFTO0FBQ3pCO0FBQ0EsZ0JBQWdCLFNBQVM7QUFDekI7QUFDQTtBQUNBLGdCQUFnQixVQUFVO0FBQzFCO0FBQ0EsZUFBZTtBQUNmO0FBQ0E7QUFDQTtBQUNBLGVBQWUsbUJBQW1CO0FBQ2xDO0FBQ0E7O0FBRUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOztBQUVBO0FBQ0E7QUFDQTtBQUNBOztBQUVBO0FBQ0E7QUFDQTs7QUFFQTtBQUNBO0FBQ0EiLCJzb3VyY2VzIjpbIndlYnBhY2s6Ly9zYWFzLXRlbXBsYXRlLW1hZ2ljdWkvLi9ub2RlX21vZHVsZXMvendpdGNoL2luZGV4LmpzPzI1YmMiXSwic291cmNlc0NvbnRlbnQiOlsiLyoqXG4gKiBAY2FsbGJhY2sgSGFuZGxlclxuICogICBIYW5kbGUgYSB2YWx1ZSwgd2l0aCBhIGNlcnRhaW4gSUQgZmllbGQgc2V0IHRvIGEgY2VydGFpbiB2YWx1ZS5cbiAqICAgVGhlIElEIGZpZWxkIGlzIHBhc3NlZCB0byBgendpdGNoYCwgYW5kIGl04oCZcyB2YWx1ZSBpcyB0aGlzIGZ1bmN0aW9u4oCZc1xuICogICBwbGFjZSBvbiB0aGUgYGhhbmRsZXJzYCByZWNvcmQuXG4gKiBAcGFyYW0gey4uLmFueX0gcGFyYW1ldGVyc1xuICogICBBcmJpdHJhcnkgcGFyYW1ldGVycyBwYXNzZWQgdG8gdGhlIHp3aXRjaC5cbiAqICAgVGhlIGZpcnN0IHdpbGwgYmUgYW4gb2JqZWN0IHdpdGggYSBjZXJ0YWluIElEIGZpZWxkIHNldCB0byBhIGNlcnRhaW4gdmFsdWUuXG4gKiBAcmV0dXJucyB7YW55fVxuICogICBBbnl0aGluZyFcbiAqL1xuXG4vKipcbiAqIEBjYWxsYmFjayBVbmtub3duSGFuZGxlclxuICogICBIYW5kbGUgdmFsdWVzIHRoYXQgZG8gaGF2ZSBhIGNlcnRhaW4gSUQgZmllbGQsIGJ1dCBpdOKAmXMgc2V0IHRvIGEgdmFsdWVcbiAqICAgdGhhdCBpcyBub3QgbGlzdGVkIGluIHRoZSBgaGFuZGxlcnNgIHJlY29yZC5cbiAqIEBwYXJhbSB7dW5rbm93bn0gdmFsdWVcbiAqICAgQW4gb2JqZWN0IHdpdGggYSBjZXJ0YWluIElEIGZpZWxkIHNldCB0byBhbiB1bmtub3duIHZhbHVlLlxuICogQHBhcmFtIHsuLi5hbnl9IHJlc3RcbiAqICAgQXJiaXRyYXJ5IHBhcmFtZXRlcnMgcGFzc2VkIHRvIHRoZSB6d2l0Y2guXG4gKiBAcmV0dXJucyB7YW55fVxuICogICBBbnl0aGluZyFcbiAqL1xuXG4vKipcbiAqIEBjYWxsYmFjayBJbnZhbGlkSGFuZGxlclxuICogICBIYW5kbGUgdmFsdWVzIHRoYXQgZG8gbm90IGhhdmUgYSBjZXJ0YWluIElEIGZpZWxkLlxuICogQHBhcmFtIHt1bmtub3dufSB2YWx1ZVxuICogICBBbnkgdW5rbm93biB2YWx1ZS5cbiAqIEBwYXJhbSB7Li4uYW55fSByZXN0XG4gKiAgIEFyYml0cmFyeSBwYXJhbWV0ZXJzIHBhc3NlZCB0byB0aGUgendpdGNoLlxuICogQHJldHVybnMge3ZvaWR8bnVsbHx1bmRlZmluZWR8bmV2ZXJ9XG4gKiAgIFRoaXMgc2hvdWxkIGNyYXNoIG9yIHJldHVybiBub3RoaW5nLlxuICovXG5cbi8qKlxuICogQHRlbXBsYXRlIHtJbnZhbGlkSGFuZGxlcn0gW0ludmFsaWQ9SW52YWxpZEhhbmRsZXJdXG4gKiBAdGVtcGxhdGUge1Vua25vd25IYW5kbGVyfSBbVW5rbm93bj1Vbmtub3duSGFuZGxlcl1cbiAqIEB0ZW1wbGF0ZSB7UmVjb3JkPHN0cmluZywgSGFuZGxlcj59IFtIYW5kbGVycz1SZWNvcmQ8c3RyaW5nLCBIYW5kbGVyPl1cbiAqIEB0eXBlZGVmIE9wdGlvbnNcbiAqICAgQ29uZmlndXJhdGlvbiAocmVxdWlyZWQpLlxuICogQHByb3BlcnR5IHtJbnZhbGlkfSBbaW52YWxpZF1cbiAqICAgSGFuZGxlciB0byB1c2UgZm9yIGludmFsaWQgdmFsdWVzLlxuICogQHByb3BlcnR5IHtVbmtub3dufSBbdW5rbm93bl1cbiAqICAgSGFuZGxlciB0byB1c2UgZm9yIHVua25vd24gdmFsdWVzLlxuICogQHByb3BlcnR5IHtIYW5kbGVyc30gW2hhbmRsZXJzXVxuICogICBIYW5kbGVycyB0byB1c2UuXG4gKi9cblxuY29uc3Qgb3duID0ge30uaGFzT3duUHJvcGVydHlcblxuLyoqXG4gKiBIYW5kbGUgdmFsdWVzIGJhc2VkIG9uIGEgZmllbGQuXG4gKlxuICogQHRlbXBsYXRlIHtJbnZhbGlkSGFuZGxlcn0gW0ludmFsaWQ9SW52YWxpZEhhbmRsZXJdXG4gKiBAdGVtcGxhdGUge1Vua25vd25IYW5kbGVyfSBbVW5rbm93bj1Vbmtub3duSGFuZGxlcl1cbiAqIEB0ZW1wbGF0ZSB7UmVjb3JkPHN0cmluZywgSGFuZGxlcj59IFtIYW5kbGVycz1SZWNvcmQ8c3RyaW5nLCBIYW5kbGVyPl1cbiAqIEBwYXJhbSB7c3RyaW5nfSBrZXlcbiAqICAgRmllbGQgdG8gc3dpdGNoIG9uLlxuICogQHBhcmFtIHtPcHRpb25zPEludmFsaWQsIFVua25vd24sIEhhbmRsZXJzPn0gW29wdGlvbnNdXG4gKiAgIENvbmZpZ3VyYXRpb24gKHJlcXVpcmVkKS5cbiAqIEByZXR1cm5zIHt7dW5rbm93bjogVW5rbm93biwgaW52YWxpZDogSW52YWxpZCwgaGFuZGxlcnM6IEhhbmRsZXJzLCAoLi4ucGFyYW1ldGVyczogUGFyYW1ldGVyczxIYW5kbGVyc1trZXlvZiBIYW5kbGVyc10+KTogUmV0dXJuVHlwZTxIYW5kbGVyc1trZXlvZiBIYW5kbGVyc10+LCAoLi4ucGFyYW1ldGVyczogUGFyYW1ldGVyczxVbmtub3duPik6IFJldHVyblR5cGU8VW5rbm93bj59fVxuICovXG5leHBvcnQgZnVuY3Rpb24gendpdGNoKGtleSwgb3B0aW9ucykge1xuICBjb25zdCBzZXR0aW5ncyA9IG9wdGlvbnMgfHwge31cblxuICAvKipcbiAgICogSGFuZGxlIG9uZSB2YWx1ZS5cbiAgICpcbiAgICogQmFzZWQgb24gdGhlIGJvdW5kIGBrZXlgLCBhIHJlc3BlY3RpdmUgaGFuZGxlciB3aWxsIGJlIGNhbGxlZC5cbiAgICogSWYgYHZhbHVlYCBpcyBub3QgYW4gb2JqZWN0LCBvciBkb2VzbuKAmXQgaGF2ZSBhIGBrZXlgIHByb3BlcnR5LCB0aGUgc3BlY2lhbFxuICAgKiDigJxpbnZhbGlk4oCdIGhhbmRsZXIgd2lsbCBiZSBjYWxsZWQuXG4gICAqIElmIGB2YWx1ZWAgaGFzIGFuIHVua25vd24gYGtleWAsIHRoZSBzcGVjaWFsIOKAnHVua25vd27igJ0gaGFuZGxlciB3aWxsIGJlXG4gICAqIGNhbGxlZC5cbiAgICpcbiAgICogQWxsIGFyZ3VtZW50cywgYW5kIHRoZSBjb250ZXh0IG9iamVjdCwgYXJlIHBhc3NlZCB0aHJvdWdoIHRvIHRoZSBoYW5kbGVyLFxuICAgKiBhbmQgaXTigJlzIHJlc3VsdCBpcyByZXR1cm5lZC5cbiAgICpcbiAgICogQHRoaXMge3Vua25vd259XG4gICAqICAgQW55IGNvbnRleHQgb2JqZWN0LlxuICAgKiBAcGFyYW0ge3Vua25vd259IFt2YWx1ZV1cbiAgICogICBBbnkgdmFsdWUuXG4gICAqIEBwYXJhbSB7Li4udW5rbm93bn0gcGFyYW1ldGVyc1xuICAgKiAgIEFyYml0cmFyeSBwYXJhbWV0ZXJzIHBhc3NlZCB0byB0aGUgendpdGNoLlxuICAgKiBAcHJvcGVydHkge0hhbmRsZXJ9IGludmFsaWRcbiAgICogICBIYW5kbGUgZm9yIHZhbHVlcyB0aGF0IGRvIG5vdCBoYXZlIGEgY2VydGFpbiBJRCBmaWVsZC5cbiAgICogQHByb3BlcnR5IHtIYW5kbGVyfSB1bmtub3duXG4gICAqICAgSGFuZGxlIHZhbHVlcyB0aGF0IGRvIGhhdmUgYSBjZXJ0YWluIElEIGZpZWxkLCBidXQgaXTigJlzIHNldCB0byBhIHZhbHVlXG4gICAqICAgdGhhdCBpcyBub3QgbGlzdGVkIGluIHRoZSBgaGFuZGxlcnNgIHJlY29yZC5cbiAgICogQHByb3BlcnR5IHtIYW5kbGVyc30gaGFuZGxlcnNcbiAgICogICBSZWNvcmQgb2YgaGFuZGxlcnMuXG4gICAqIEByZXR1cm5zIHt1bmtub3dufVxuICAgKiAgIEFueXRoaW5nLlxuICAgKi9cbiAgZnVuY3Rpb24gb25lKHZhbHVlLCAuLi5wYXJhbWV0ZXJzKSB7XG4gICAgLyoqIEB0eXBlIHtIYW5kbGVyfHVuZGVmaW5lZH0gKi9cbiAgICBsZXQgZm4gPSBvbmUuaW52YWxpZFxuICAgIGNvbnN0IGhhbmRsZXJzID0gb25lLmhhbmRsZXJzXG5cbiAgICBpZiAodmFsdWUgJiYgb3duLmNhbGwodmFsdWUsIGtleSkpIHtcbiAgICAgIC8vIEB0cy1leHBlY3QtZXJyb3IgSW5kZXhhYmxlLlxuICAgICAgY29uc3QgaWQgPSBTdHJpbmcodmFsdWVba2V5XSlcbiAgICAgIC8vIEB0cy1leHBlY3QtZXJyb3IgSW5kZXhhYmxlLlxuICAgICAgZm4gPSBvd24uY2FsbChoYW5kbGVycywgaWQpID8gaGFuZGxlcnNbaWRdIDogb25lLnVua25vd25cbiAgICB9XG5cbiAgICBpZiAoZm4pIHtcbiAgICAgIHJldHVybiBmbi5jYWxsKHRoaXMsIHZhbHVlLCAuLi5wYXJhbWV0ZXJzKVxuICAgIH1cbiAgfVxuXG4gIG9uZS5oYW5kbGVycyA9IHNldHRpbmdzLmhhbmRsZXJzIHx8IHt9XG4gIG9uZS5pbnZhbGlkID0gc2V0dGluZ3MuaW52YWxpZFxuICBvbmUudW5rbm93biA9IHNldHRpbmdzLnVua25vd25cblxuICAvLyBAdHMtZXhwZWN0LWVycm9yOiBtYXRjaGVzIVxuICByZXR1cm4gb25lXG59XG4iXSwibmFtZXMiOltdLCJzb3VyY2VSb290IjoiIn0=\n//# sourceURL=webpack-internal:///(rsc)/./node_modules/zwitch/index.js\n");

/***/ })

};
;